"""
多轮对话处理器

处理用户多次输入、信息纠正、累积上下文分析
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db_manager
from ..database.models import AnalysisMessage, AnalysisSnapshot
from .workflow import get_workflow


class MultiTurnConversationHandler:
    """多轮对话处理器"""

    def __init__(self):
        self.db = get_db_manager()

    async def handle_user_message(
        self,
        session_id: str,
        content: str,
        content_type: str = "text",
        correction_target: Optional[int] = None,
        user_id: Optional[str] = None,
        chip_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息的主流程

        Args:
            session_id: 会话ID
            content: 消息内容
            content_type: 内容类型 (text, log, correction_data)
            correction_target: 如果是纠正，指定要纠正的消息ID
            user_id: 用户ID
            chip_model: 芯片型号

        Returns:
            处理结果
        """
        try:
            # 1. 获取会话上下文
            context = await self._get_conversation_context(session_id)

            # 2. 确定序列号
            next_sequence = context["last_sequence"] + 1

            # 3. 处理纠正消息
            if correction_target:
                context = await self._apply_correction(
                    context,
                    correction_target,
                    content
                )
                message_type = "correction"
            else:
                message_type = "user_input"
                # 4. 添加新消息到上下文
                context = await self._append_message(context, content, content_type)

            # 5. 保存用户消息
            user_message = await self._save_message(
                session_id=session_id,
                message_type=message_type,
                sequence_number=next_sequence,
                content=content,
                content_type=content_type,
                correction_target=correction_target,
                user_id=user_id
            )

            # 更新上下文的 last_sequence
            context["last_sequence"] = next_sequence

            # 6. 将新消息添加到上下文（用于后续分析和响应生成）
            print(f"[DEBUG] Before append - messages count: {len(context.get('messages', []))}, id of messages: {id(context.get('messages'))}")
            context["messages"].append({
                "message_id": user_message["message_id"],
                "message_type": message_type,
                "sequence_number": next_sequence,
                "content": content,
                "content_type": content_type,
                "is_correction": correction_target is not None,
                "corrected_message_id": correction_target,
                "extracted_fields": {}
            })
            print(f"[DEBUG] After append - messages count: {len(context.get('messages', []))}, context id: {id(context)}")

            # 调试日志
            logger.info(f"[MultiTurnHandler] 消息添加后的上下文 - messages数量: {len(context['messages'])}, next_sequence: {next_sequence}")

            # 7. 触发重新分析
            analysis_result = await self._analyze_with_context(
                session_id,
                context,
                chip_model or context.get("chip_model", "XC9000"),
                user_id
            )

            # 8. 保存快照
            await self._save_snapshot(
                session_id=session_id,
                message_id=user_message["message_id"],
                accumulated_context=context,
                analysis_result=analysis_result
            )

            # 9. 生成系统响应
            # 计算用户消息数（当前序列号+1）/2
            user_message_count = (next_sequence + 1) // 2
            print(f"[DEBUG] user_message_count calculation: next_sequence={next_sequence}, user_message_count={user_message_count}")
            response = await self._generate_response(
                context,
                analysis_result,
                user_message_count
            )

            # 10. 保存系统响应消息
            await self._save_message(
                session_id=session_id,
                message_type="system_response",
                sequence_number=next_sequence + 1,
                content=response,
                content_type="text"
            )

            return {
                "success": True,
                "message_id": user_message["message_id"],
                "sequence_number": next_sequence,
                "analysis_result": analysis_result,
                "system_response": response,
                "context_updated": True
            }

        except Exception as e:
            logger.error(f"[MultiTurnHandler] 处理消息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message_id": None,
                "analysis_result": None
            }

    async def _get_conversation_context(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """获取会话的累积上下文"""
        messages = await self.db.get_session_messages(session_id)

        # 构建累积上下文
        context = {
            "session_id": session_id,
            "messages": [],
            "accumulated_logs": [],
            "accumulated_features": {
                "error_codes": [],
                "modules": [],
                "domains": []
            },
            "corrections": {},
            "last_sequence": 0,
            "chip_model": None
        }

        # 跟踪已被纠正的消息ID
        corrected_message_ids = set()

        for msg in messages:
            context["last_sequence"] = max(context["last_sequence"], msg.sequence_number)

            # 记录纠正关系（转换为字典以避免序列化问题）
            if msg.is_correction and msg.corrected_message_id:
                context["corrections"][msg.corrected_message_id] = {
                    "message_id": msg.message_id,
                    "message_type": msg.message_type,
                    "sequence_number": msg.sequence_number,
                    "content": msg.content,
                    "content_type": msg.content_type,
                    "is_correction": msg.is_correction,
                    "corrected_message_id": msg.corrected_message_id,
                    "extracted_fields": msg.extracted_fields or {}
                }
                corrected_message_ids.add(msg.corrected_message_id)
                continue  # 不将纠正信息本身添加到累积上下文

            # 跳过已��纠正的消息
            if msg.message_id in corrected_message_ids:
                continue

            # 累积有效消息（转换为字典以避免序列化问题）
            context["messages"].append({
                "message_id": msg.message_id,
                "message_type": msg.message_type,
                "sequence_number": msg.sequence_number,
                "content": msg.content,
                "content_type": msg.content_type,
                "is_correction": msg.is_correction,
                "corrected_message_id": msg.corrected_message_id,
                "extracted_fields": msg.extracted_fields or {}
            })

            if msg.content_type == "log":
                context["accumulated_logs"].append(msg.content)

            # 提取并累积特征
            if msg.extracted_fields:
                self._merge_features(
                    context["accumulated_features"],
                    msg.extracted_fields
                )

            # 如果有芯片型号，使用最新的
            if msg.extracted_fields and "chip_model" in msg.extracted_fields:
                context["chip_model"] = msg.extracted_fields["chip_model"]

        return context

    async def _apply_correction(
        self,
        context: Dict[str, Any],
        target_message_id: int,
        corrected_content: str
    ) -> Dict[str, Any]:
        """应用纠正到上下文"""
        logger.info(f"[MultiTurnHandler] 应用纠正: 目标消息ID={target_message_id}")

        # 标记原消息被纠正
        context["corrections"][target_message_id] = {
            "corrected_at": datetime.utcnow().isoformat(),
            "corrected_content": corrected_content
        }

        # 从累积信息中移除原消息的贡献
        # 这里需要重新计算上下文，暂时简化处理
        # 实际实现中应该撤销原消息的特征贡献

        return context

    async def _append_message(
        self,
        context: Dict[str, Any],
        content: str,
        content_type: str
    ) -> Dict[str, Any]:
        """添加新消息到上下文"""
        if content_type == "log":
            context["accumulated_logs"].append(content)

        # 这里可以添加特征提取逻辑
        # extracted_features = await self._extract_features(content, content_type)
        # self._merge_features(context["accumulated_features"], extracted_features)

        return context

    def _merge_features(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any]
    ) -> None:
        """合并特征"""
        for key, value in new.items():
            if isinstance(value, list):
                # 数组类型合并（去重）
                if key not in existing:
                    existing[key] = []
                existing[key] = list(set(existing[key] + value))
            elif isinstance(value, dict):
                # 字典类型合并
                if key not in existing:
                    existing[key] = {}
                existing[key].update(value)
            else:
                # 其他类型直接覆盖
                existing[key] = value

    async def _analyze_with_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        chip_model: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """基于累积上下文进行分析"""
        # 1. 合并所有日志
        combined_log = "\n".join(context["accumulated_logs"])

        # 如果没有日志，使用原始输入
        if not combined_log:
            # 尝试从最新消息获取
            if context["messages"]:
                last_message = context["messages"][-1]
                # 兼容字典格式和SQLAlchemy对象格式
                combined_log = last_message.get("content") if isinstance(last_message, dict) else last_message.content

        # 2. 调用工作流分析
        workflow = get_workflow()
        result = await workflow.run(
            chip_model=chip_model,
            raw_log=combined_log,
            session_id=session_id,
            user_id=user_id,
            infer_threshold=0.7
        )

        return result

    async def _save_message(
        self,
        session_id: str,
        message_type: str,
        sequence_number: int,
        content: str,
        content_type: str = "text",
        correction_target: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """保存消息到数据库"""
        async with self.db._session_factory() as session:
            message = AnalysisMessage(
                session_id=session_id,
                message_type=message_type,
                sequence_number=sequence_number,
                content=content,
                content_type=content_type,
                is_correction=(correction_target is not None),
                corrected_message_id=correction_target,
                message_metadata={
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )

            session.add(message)
            await session.flush()

            message_id = message.message_id
            await session.commit()

            return {
                "message_id": message_id,
                "sequence_number": sequence_number
            }

    async def _save_snapshot(
        print("[DEBUG] _save_snapshot CALLED with latest code!!!")
        self,
        session_id: str,
        message_id: int,
        accumulated_context: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> None:
        """保存分析快照"""
        # 调试日志：保存快照时的上下文状态
        messages_list = accumulated_context.get("messages", [])
        print(f"[DEBUG] _save_snapshot - messages数量: {len(messages_list)}, message_id: {message_id}, context id: {id(accumulated_context)}")
        logger.info(f"[MultiTurnHandler] _save_snapshot - messages数量: {len(messages_list)}, message_id: {message_id}")

        # 将SQLAlchemy对象转换为字典以便JSON序列化
        serializable_messages = []
        for msg in messages_list:
            if isinstance(msg, dict):
                # 已经是字典格式，直接使用
                serializable_messages.append(msg)
            else:
                # SQLAlchemy对象，需要转换
                serializable_messages.append({
                    "message_id": msg.message_id,
                    "message_type": msg.message_type,
                    "sequence_number": msg.sequence_number,
                    "content": msg.content,
                    "content_type": msg.content_type,
                    "is_correction": msg.is_correction,
                    "corrected_message_id": msg.corrected_message_id,
                    "extracted_fields": msg.extracted_fields or {}
                })

        # 将corrections字典中的SQLAlchemy对象也转换为字典
        serializable_corrections = {}
        for msg_id, correction_msg in accumulated_context.get("corrections", {}).items():
            if isinstance(correction_msg, dict):
                serializable_corrections[msg_id] = correction_msg
            else:
                # SQLAlchemy对象，需要转换
                serializable_corrections[msg_id] = {
                    "message_id": correction_msg.message_id,
                    "message_type": correction_msg.message_type,
                    "sequence_number": correction_msg.sequence_number,
                    "content": correction_msg.content,
                    "content_type": correction_msg.content_type,
                    "is_correction": correction_msg.is_correction,
                    "corrected_message_id": correction_msg.corrected_message_id,
                    "extracted_fields": correction_msg.extracted_fields or {}
                }

        serializable_context = {
            "session_id": accumulated_context.get("session_id"),
            "messages": serializable_messages,
            "accumulated_logs": accumulated_context.get("accumulated_logs", []),
            "accumulated_features": accumulated_context.get("accumulated_features", {}),
            "corrections": serializable_corrections,
            "last_sequence": accumulated_context.get("last_sequence", 0),
            "chip_model": accumulated_context.get("chip_model")
        }

        logger.info(f"[MultiTurnHandler] _save_snapshot - 序列化后messages数量: {len(serializable_context['messages'])}")

        # 调��：检查serializable_context中是否还有SQLAlchemy对象
        print(f"[DEBUG] Before DB insert - checking serializable_context for SQLAlchemy objects")
        for key, value in serializable_context.items():
            if key == "messages":
                for i, msg in enumerate(value):
                    if not isinstance(msg, dict):
                        print(f"[DEBUG] WARNING: Found non-dict in messages at index {i}: {type(msg)}")
            elif key == "corrections":
                for k, v in value.items():
                    if not isinstance(v, dict):
                        print(f"[DEBUG] WARNING: Found non-dict in corrections[{k}]: {type(v)}")

        # 确保完全JSON可序列化
        import json
        try:
            json.dumps(serializable_context)
            print(f'[DEBUG] JSON serialization successful')
        except Exception as e:
            print(f'[DEBUG] Serialization failed: {e}')
            # 强制转换所有SQLAlchemy对象
            for key, value in serializable_context.items():
                if key == 'messages':
                    for i, msg in enumerate(value):
                        if hasattr(msg, '__table__'):
                            serializable_context['messages'][i] = {
                                c.name: getattr(msg, c.name) 
                                for c in msg.__table__.columns
                            }
                            print(f'[DEBUG] Converted message {i} to dict')
                elif key == 'corrections':
                    for k, v in value.items():
                        if hasattr(v, '__table__'):
                            serializable_context['corrections'][k] = {
                                c.name: getattr(v, c.name) 
                                for c in v.__table__.columns
                            }
                            print(f'[DEBUG] Converted correction {k} to dict')

        async with self.db._session_factory() as session:
            snapshot = AnalysisSnapshot(
                session_id=session_id,
                message_id=message_id,
                accumulated_context=serializable_context,
                analysis_result=analysis_result
            )

            session.add(snapshot)
            await session.commit()



    async def _save_snapshot(
        self,
        session_id: str,
        message_id: int,
        accumulated_context: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> None:
        """保存分析快照"""
        import json
        
        # 深度转换函数，确保所有SQLAlchemy对象被转换
        def deep_convert(obj):
            if hasattr(obj, '__table__'):  # SQLAlchemy对象
                return {c.name: deep_convert(getattr(obj, c.name)) for c in obj.__table__.columns}
            elif isinstance(obj, dict):
                return {k: deep_convert(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [deep_convert(item) for item in obj]
            else:
                return obj
        
        # 深度转换整个context
        try:
            serializable_context = deep_convert(accumulated_context)
            # 验证可以JSON序列化
            json.dumps(serializable_context)
            print(f'[DEBUG] Serialization successful')
        except Exception as e:
            print(f'[DEBUG] Serialization failed: {e}')
            # 作为后备，创建最小化的context
            serializable_context = {
                'session_id': accumulated_context.get('session_id'),
                'messages': [],
                'accumulated_logs': accumulated_context.get('accumulated_logs', []),
                'accumulated_features': accumulated_context.get('accumulated_features', {}),
                'corrections': {},
                'last_sequence': accumulated_context.get('last_sequence', 0),
                'chip_model': accumulated_context.get('chip_model')
            }
        
        async with self.db._session_factory() as session:
            snapshot = AnalysisSnapshot(
                session_id=session_id,
                message_id=message_id,
                accumulated_context=serializable_context,
                analysis_result=analysis_result
            )
            session.add(snapshot)
            await session.commit()

    async def _generate_response(
        self,
        context: Dict[str, Any],
        analysis_result: Dict[str, Any],
        user_message_count: int
    ) -> str:
        """生成系统响应"""
        # 基于分析结果生成对话式响应
        need_expert = analysis_result.get("need_expert", False)
        confidence = analysis_result.get("final_root_cause", {}).get("confidence", 0)

        print(f"[DEBUG] _generate_response: user_message_count={user_message_count}, confidence={confidence}")
        logger.info(f"[MultiTurnHandler] 生成响应 - user_message_count: {user_message_count}, confidence: {confidence}")

        if user_message_count == 1:
            # 首次分析
            if confidence < 0.5:
                return "当前信息不足以做出准确判断，建议提供更多日志信息，如：错误码、寄存器值、故障发生时间等。"
            elif need_expert:
                return f"初步分析完成，置信度{confidence*100:.1f}%。由于置信度较低，建议专家介入确认。您可以继续提供更多信息以提高分析准确性。"
            else:
                return f"分析完成，置信度{confidence*100:.1f}%。失效域为{analysis_result.get('final_root_cause', {}).get('failure_domain')}。如需补充信息，可继续提供。"
        else:
            # 多轮对话
            if confidence < 0.5:
                return f"已收到您提供的信息（共{user_message_count}条输入），但置信度仍较低({confidence*100:.1f}%)。请提供更多关键信息，如：完整的错误日志、环境参数、操作步骤等。"
            elif need_expert:
                return f"分析更新完成，置信度{confidence*100:.1f}%。基于{user_message_count}条输入的分析仍建议专家确认。您可以继续补充信息或请求专家介入。"
            else:
                return f"分析更新完成，置信度{confidence*100:.1f}%。失效域确定为{analysis_result.get('final_root_cause', {}).get('failure_domain')}。如有其他信息需要补充，请继续提供。"

    async def get_conversation_history(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """获取对话历史"""
        messages = await self.db.get_session_messages(session_id)

        # 获取最新分析结果
        latest_snapshot = await self.db.get_latest_snapshot(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "messages": [
                {
                    "message_id": msg.message_id,
                    "message_type": msg.message_type,
                    "sequence_number": msg.sequence_number,
                    "content": msg.content,
                    "content_type": msg.content_type,
                    "created_at": msg.created_at.isoformat(),
                    "is_correction": msg.is_correction,
                    "corrected_message_id": msg.corrected_message_id,
                    "extracted_fields": msg.extracted_fields
                }
                for msg in messages
            ],
            "current_analysis": latest_snapshot["analysis_result"] if latest_snapshot else None,
            "total_messages": len(messages)
        }

    async def get_analysis_timeline(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """获取分析时间线"""
        snapshots = await self.db.get_session_snapshots(session_id)

        timeline = []
        for snapshot in snapshots:
            result = snapshot.analysis_result
            timeline_entry = {
                "snapshot_id": snapshot.snapshot_id,
                "message_id": snapshot.message_id,
                "created_at": snapshot.created_at.isoformat(),
                "analysis_summary": {
                    "failure_domain": result.get("final_root_cause", {}).get("failure_domain"),
                    "confidence": result.get("final_root_cause", {}).get("confidence", 0),
                    "need_expert": result.get("need_expert", False),
                    "root_cause": result.get("final_root_cause", {}).get("root_cause")
                },
                "accumulated_info_count": len(snapshot.accumulated_context.get("messages", []))
            }
            timeline.append(timeline_entry)

        return {
            "success": True,
            "session_id": session_id,
            "timeline": timeline,
            "total_entries": len(timeline)
        }


# 全局实例
multi_turn_handler = MultiTurnConversationHandler()
