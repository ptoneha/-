-- ========================================
-- 管理系统数据库扩展
-- ========================================

-- 1. 管理员用户表
CREATE TABLE IF NOT EXISTS public.admin_user (
    user_id       BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     VARCHAR(100),
    email         VARCHAR(100) UNIQUE,
    role          VARCHAR(20) DEFAULT 'admin' CHECK (role IN ('superadmin', 'admin', 'editor', 'viewer')),
    is_active     BOOLEAN DEFAULT true,
    created_at    TIMESTAMP DEFAULT now(),
    updated_at    TIMESTAMP DEFAULT now(),
    last_login_at TIMESTAMP
);

-- 默认管理员账号 (密码: admin123)
INSERT INTO public.admin_user (username, password_hash, full_name, role)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lE7X9fKJ5jO6', '系统管理员', 'superadmin')
ON CONFLICT (username) DO NOTHING;

-- 2. 操作审计日志表
CREATE TABLE IF NOT EXISTS public.audit_log (
    log_id        BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES public.admin_user(user_id) ON DELETE SET NULL,
    username      VARCHAR(50),
    action        VARCHAR(50) NOT NULL,  -- create, update, delete, export, login, logout
    resource_type VARCHAR(50),           -- doc, chunk, question, user
    resource_id   BIGINT,
    details       JSONB,                 -- 操作详情
    ip_address    VARCHAR(50),
    user_agent    TEXT,
    created_at    TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON public.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON public.audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON public.audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON public.audit_log(created_at DESC);

-- 3. 知识库分类表
CREATE TABLE IF NOT EXISTS public.kb_category (
    category_id   BIGSERIAL PRIMARY KEY,
    name          VARCHAR(100) UNIQUE NOT NULL,
    description   TEXT,
    parent_id     BIGINT REFERENCES public.kb_category(category_id) ON DELETE CASCADE,
    sort_order    INT DEFAULT 0,
    created_at    TIMESTAMP DEFAULT now()
);

-- 4. 文档分类关联表
CREATE TABLE IF NOT EXISTS public.doc_category (
    doc_id        BIGINT REFERENCES public.doc(doc_id) ON DELETE CASCADE,
    category_id   BIGINT REFERENCES public.kb_category(category_id) ON DELETE CASCADE,
    PRIMARY KEY (doc_id, category_id)
);

-- 5. 标签表
CREATE TABLE IF NOT EXISTS public.tag (
    tag_id        BIGSERIAL PRIMARY KEY,
    name          VARCHAR(50) UNIQUE NOT NULL,
    color         VARCHAR(20),
    created_at    TIMESTAMP DEFAULT now()
);

-- 6. 分片标签关联表
CREATE TABLE IF NOT EXISTS public.chunk_tag (
    chunk_id      BIGINT REFERENCES public.chunk(chunk_id) ON DELETE CASCADE,
    tag_id        BIGINT REFERENCES public.tag(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (chunk_id, tag_id)
);

-- 7. 扩展doc表 (添加管理字段)
ALTER TABLE public.doc ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT true;
ALTER TABLE public.doc ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();
ALTER TABLE public.doc ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- 8. 扩展chunk表 (添加管理字段)
ALTER TABLE public.chunk ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;
ALTER TABLE public.chunk ADD COLUMN IF NOT EXISTS quality_score INT DEFAULT 0 CHECK (quality_score >= 0 AND quality_score <= 100);
ALTER TABLE public.chunk ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();
ALTER TABLE public.chunk ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- 9. 扩展question表 (添加管理字段)
ALTER TABLE public.question ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT true;
ALTER TABLE public.question ADD COLUMN IF NOT EXISTS usage_count INT DEFAULT 0;
ALTER TABLE public.question ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now();
ALTER TABLE public.question ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- 10. 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_doc_updated_at BEFORE UPDATE ON public.doc
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunk_updated_at BEFORE UPDATE ON public.chunk
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_updated_at BEFORE UPDATE ON public.question
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_user_updated_at BEFORE UPDATE ON public.admin_user
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 11. 创建统计视图
CREATE OR REPLACE VIEW v_admin_stats AS
SELECT
    (SELECT COUNT(*) FROM public.doc WHERE deleted_at IS NULL) as total_docs,
    (SELECT COUNT(*) FROM public.chunk WHERE deleted_at IS NULL) as total_chunks,
    (SELECT COUNT(*) FROM public.question WHERE deleted_at IS NULL) as total_questions,
    (SELECT COUNT(*) FROM public.admin_user WHERE is_active = true) as active_admins,
    (SELECT COUNT(*) FROM public.audit_log WHERE created_at > now() - interval '24 hours') as logs_24h;

-- 12. 创建文档统计视图
CREATE OR REPLACE VIEW v_doc_stats AS
SELECT
    d.doc_id,
    d.title,
    d.source,
    d.created_at,
    COUNT(c.chunk_id) as chunk_count,
    AVG(c.quality_score) as avg_quality,
    SUM(c.tokens) as total_tokens
FROM public.doc d
LEFT JOIN public.chunk c ON d.doc_id = c.doc_id AND c.deleted_at IS NULL
WHERE d.deleted_at IS NULL
GROUP BY d.doc_id, d.title, d.source, d.created_at;

