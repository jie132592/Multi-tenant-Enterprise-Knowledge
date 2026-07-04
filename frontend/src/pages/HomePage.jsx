import { Row, Col, Card, Statistic } from 'antd';
import { UserOutlined, TeamOutlined, BookOutlined, MessageOutlined } from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>欢迎使用 Mini KB</h1>
      <p style={{ marginBottom: 32, color: '#666' }}>
        您好，{user?.username}！{user?.is_super_admin ? '您是超级管理员' : '您是租户管理员'}。
      </p>

      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="当前租户"
              value={user?.tenant_id}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="用户角色"
              value={user?.is_super_admin ? '超级管理员' : '普通用户'}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="知识库"
              value="-"
              prefix={<BookOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="对话会话"
              value="-"
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 16 }}>快速开始</h2>
        <Row gutter={16}>
          <Col span={8}>
            <Card title="创建知识库" style={{ height: 180 }}>
              <p style={{ color: '#666' }}>为您的团队创建一个知识库，用于存储和管理文档。</p>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="上传文档" style={{ height: 180 }}>
              <p style={{ color: '#666' }}>支持 PDF、Word、文本等格式，自动分块和向量化。</p>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="开始对话" style={{ height: 180 }}>
              <p style={{ color: '#666' }}>基于知识库内容，与 AI 进行智能对话和问答。</p>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
}
