"""
Agent1 - 报告生成Agent
负责基于分析结果生成标准化报告
"""

from typing import Dict, List, Any, Optional
from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path
import asyncio
from datetime import datetime
from loguru import logger


class ReportGenerator:
    """报告生成器类"""

    def __init__(self):
        """初始化报告生成器"""
        self.name = "ReportGenerator"
        self.description = "生成芯片失效分析报告"

        # 设置Jinja2模板环境
        self.template_dir = Path(__file__).parent.parent.parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False
        )

    async def generate(
        self,
        analysis_id: str,
        analysis_result: Dict[str, Any],
        report_type: str = "html",
        template_name: str = "default"
    ) -> Dict[str, Any]:
        """
        生成分析报告

        Args:
            analysis_id: 分析ID
            analysis_result: 分析结果字典
            report_type: 报告类型（html/pdf）
            template_name: 模板名称

        Returns:
            报告生成结果
        """
        logger.info(f"[{self.name}] 开始生成报告 - 分析ID: {analysis_id}")

        try:
            # 准备报告数据
            report_data = await self._prepare_report_data(analysis_id, analysis_result)

            # 生成报告内容
            if report_type == "html":
                content = await self._generate_html_report(template_name, report_data)
            elif report_type == "pdf":
                content = await self._generate_pdf_report(template_name, report_data)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")

            # 保存报告
            report_path = await self._save_report(analysis_id, report_type, content)

            logger.info(f"[{self.name}] 报告生成完成 - 路径: {report_path}")

            return {
                "success": True,
                "report_type": report_type,
                "report_path": report_path,
                "report_data": report_data,
                "generation_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[{self.name}] 报告生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis_id": analysis_id
            }

    async def _prepare_report_data(
        self,
        analysis_id: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备报告数据"""

        fault_features = analysis_result.get("fault_features", {})
        reasoning_result = analysis_result.get("reasoning_sources", {})
        failure_domain = analysis_result.get("failure_domain", "Unknown")
        root_cause = analysis_result.get("root_cause", "Unknown")
        confidence = analysis_result.get("confidence", 0.0)

        # Get module name from fault_features or analysis_result
        module = "Unknown"
        if fault_features.get("modules"):
            module = fault_features["modules"][0] if fault_features["modules"] else "Unknown"
        elif analysis_result.get("failure_module"):
            module = analysis_result["failure_module"]

        return {
            "analysis_id": analysis_id,
            "chip_model": analysis_result.get("chip_model", "Unknown"),
            "created_at": analysis_result.get("created_at", datetime.now().isoformat()),
            # Top-level fields for template compatibility
            "failure_domain": failure_domain,
            "module": module,
            "root_cause": root_cause,
            "confidence": confidence,
            "fault_features": {
                "error_codes": fault_features.get("error_codes", []),
                "registers": fault_features.get("registers", {}),
                "fault_description": fault_features.get("fault_description", ""),
                "timestamp": fault_features.get("timestamp", ""),
                "modules": fault_features.get("modules", []),
                "domain": fault_features.get("failure_domain", "Unknown")
            },
            "reasoning_result": {
                "failure_domain": failure_domain,
                "root_cause": root_cause,
                "root_cause_category": analysis_result.get("root_cause_category", "Unknown"),
                "confidence": confidence,
                "reasoning_sources": {
                    "chip_tool": {
                        "used": "chip_tool" in reasoning_result,
                        "result": reasoning_result.get("chip_tool", {})
                    },
                    "knowledge_graph": {
                        "used": "knowledge_graph" in reasoning_result,
                        "result": reasoning_result.get("knowledge_graph", {})
                    },
                    "case_match": {
                        "used": "case_match" in reasoning_result,
                        "result": reasoning_result.get("case_match", {})
                    }
                },
                "has_conflict": analysis_result.get("has_conflict", False),
                "need_expert": analysis_result.get("need_expert", False),
                "similar_cases": analysis_result.get("similar_cases", [])
            },
            "recommendations": self._generate_recommendations(analysis_result)
        }

    def _generate_recommendations(
        self,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成建议"""

        recommendations = {
            "immediate": [],
            "follow_up": [],
            "long_term": []
        }

        confidence = analysis_result.get("confidence", 0.0)
        failure_domain = analysis_result.get("failure_domain", "unknown")

        # 根据置信度生成建议
        if confidence >= 0.8:
            recommendations["immediate"].append(
                "分析置信度高（{confidence:.0%}），建议直接采用分析结果"
            )
        elif confidence >= 0.6:
            recommendations["immediate"].append(
                "分析置信度中等（{confidence:.0%}），建议参考分析结果并验证"
            )
        else:
            recommendations["immediate"].append(
                f"分析置信度较低（{confidence:.0%}），强烈建议专家复核"
            )

        # 根据失效域生成建议
        if failure_domain == "compute":
            recommendations["immediate"].append(
                "建议检查CPU核心状态和寄存器配置"
            )
        elif failure_domain == "cache":
            recommendations["immediate"].append(
                "建议检查缓存一致性协议（HA）状态"
            )
        elif failure_domain == "memory":
            recommendations["immediate"].append(
                "建议检查DDR/HBM控制器和内存接口"
            )

        # 根因建议
        root_cause = analysis_result.get("root_cause", "")
        if root_cause:
            recommendations["follow_up"].append(f"针对根因：{root_cause}")

        return recommendations

    async def _generate_html_report(
        self,
        template_name: str,
        report_data: Dict[str, Any]
    ) -> str:
        """生成HTML报告"""

        try:
            template = self.env.get_template(f"{template_name}.html")
            return template.render(**report_data)
        except Exception as e:
            logger.error(f"[{self.name}] HTML报告生成失败: {str(e)}")
            # 返回备用简单HTML
            return self._generate_fallback_html(report_data)

    def _generate_fallback_html(self, report_data: Dict[str, Any]) -> str:
        """生成备用HTML报告"""

        features = report_data.get("fault_features", {})
        reasoning = report_data.get("reasoning_result", {})

        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>芯片失效分析报告 - {report_data['analysis_id']}</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }}
                .header {{
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                h1 {{
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    background: #ecf0f1;
                    border-radius: 5px;
                }}
                .section-title {{
                    color: #3498db;
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                }}
                .info-box {{
                    background: #d5f4e6;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }}
                .warning-box {{
                    background: #ffeaa7;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }}
                .confidence-bar {{
                    height: 20px;
                    background: #ecf0f1;
                    border-radius: 10px;
                    overflow: hidden;
                    margin: 15px 0;
                }}
                .confidence-fill {{
                    height: 100%;
                    background: {self._get_confidence_color(report_data['reasoning_result'].get('confidence', 0.5))};
                    transition: width 0.3s;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                td {{
                    padding: 8px;
                    border: 1px solid #dee2e6;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .badge-success {{ background: #28a745; color: white; }}
                .badge-warning {{ background: #ffc107; color: #856404; }}
                .badge-error {{ background: #dc3545; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>芯片失效分析报告</h1>
                <table>
                    <tr><td>分析ID:</td><td>{report_data['analysis_id']}</td></tr>
                    <tr><td>芯片型号:</td><td>{report_data['chip_model']}</td></tr>
                    <tr><td>分析时间:</td><td>{report_data['analysis_timestamp']}</td></tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">故障特征</div>
                <div class="info-box">
                    <p><strong>错误码:</strong> {', '.join(features.get('error_codes', []))}</p>
                    <p><strong>故障描述:</strong> {features.get('fault_description', 'N/A')}</p>
                    <p><strong>时间戳:</strong> {features.get('timestamp', 'N/A')}</p>
                    <p><strong>模块:</strong> {', '.join(features.get('modules', []))}</p>
                </div>
            </div>

            <div class="section">
                <div class="section-title">推理结果</div>
                <div class="info-box">
                    <p><strong>失效域:</strong> {reasoning.get('failure_domain', 'Unknown')}</p>
                    <p><strong>根本原因:</strong> {reasoning.get('root_cause', 'Unknown')}</p>
                    <p><strong>置信度:</strong> {reasoning.get('confidence', 0):.0%}</p>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {reasoning.get('confidence', 0) * 100}%"></div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">推理源信息</div>
                {self._format_reasoning_sources(reasoning.get('reasoning_sources', {}))}
            </div>

            {self._format_recommendations(report_data.get('recommendations', {}))}

            <div class="section">
                <div class="section-title">报告信息</div>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>分析ID: {report_data['analysis_id']}</p>
                <p>系统版本: 1.0.0</p>
            </div>
        </body>
        </html>
        """

    def _format_reasoning_sources(self, sources: Dict[str, Any]) -> str:
        """格式化推理源信息"""

        html = '<div class="info-box">'

        if sources.get("chip_tool", {}).get("used"):
            html += f"<p><strong>芯片工具:</strong> {sources['chip_tool']['used']}</p>"

        if sources.get("knowledge_graph", {}).get("used"):
            result = sources["knowledge_graph"]["result"]
            html += f"<p><strong>知识图谱:</strong> {sources['knowledge_graph']['used']}</p>"
            html += f"<ul>"
            for reason in result.get("reasoning", []):
                html += f"<li>{reason}</li>"
            html += "</ul>"

        if sources.get("case_match", {}).get("used"):
            result = sources["case_match"]["result"]
            similarity = result.get("similarity", 0.0)
            html += f"<p><strong>案例匹配:</strong> 相似度 {similarity:.2f}</p>"
            if result.get("root_cause"):
                html += f"<p><strong>匹配案例根因:</strong> {result['root_cause']}</p>"

        html += "</div>"
        return html

    def _format_recommendations(self, recommendations: Dict[str, Any]) -> str:
        """格式化建议"""

        html = '<div class="section">'

        html += '<div class="section-title">建议</div>'

        if recommendations.get("immediate"):
            html += '<div class="warning-box"><strong>立即执行:</strong><ul>'
            for rec in recommendations["immediate"]:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"

        if recommendations.get("follow_up"):
            html += '<div class="info-box"><strong>后续跟进:</strong><ul>'
            for rec in recommendations["follow_up"]:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"

        html += "</div>"
        return html

    def _get_confidence_color(self, confidence: float) -> str:
        """根据置信度返回颜色"""
        if confidence >= 0.8:
            return "#28a745"  # 绿色
        elif confidence >= 0.6:
            return "#ffc107"  # 黄色
        else:
            return "#dc3545"  # 红色

    async def _generate_pdf_report(
        self,
        template_name: str,
        report_data: Dict[str, Any]
    ) -> str:
        """生成PDF报告"""

        # 先生成HTML
        html_content = await self._generate_html_report(template_name, report_data)

        # 使用WeasyPrint转换为PDF（简化版本，需要安装库）
        # 这里返回HTML，PDF转换需要额外配置
        return html_content

    async def _save_report(
        self,
        analysis_id: str,
        report_type: str,
        content: str
    ) -> str:
        """保存报告到文件"""

        from src.config.settings import get_settings
        settings = get_settings()

        # 确保报告目录存在
        reports_dir = Path(settings.REPORTS_DIR)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{analysis_id}_{report_type}_{timestamp}.html"
        file_path = reports_dir / filename

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"[{self.name}] 报告已保存: {file_path}")

        return str(file_path)
