-- 添加处理时长相关���段到 analysis_results 表
-- 执行时间: 2026-02-21

ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS processing_duration NUMERIC(10, 3),
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE;

-- 添加注释
COMMENT ON COLUMN analysis_results.processing_duration IS '分析处理时长（秒）';
COMMENT ON COLUMN analysis_results.started_at IS '分析开始时间';
