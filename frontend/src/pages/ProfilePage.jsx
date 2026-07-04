import { Card, Descriptions, Tag } from 'antd';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 style={{ fontSize: 20, marginBottom: 24 }}>个人设置</h1>

      <Card title="基本信息">
        <Descriptions column={2}>
          <Descriptions.Item label="用户ID">{user?.id}</Descriptions.Item>
          <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
          <Descriptions.Item label="租户ID">{user?.tenant_id}</Descriptions.Item>
          <Descriptions.Item label="用户角色">
            {user?.is_super_admin ? <Tag color="red">超级管理员</Tag> : <Tag color="blue">普通用户</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label="账号状态">
            {user?.is_active === 1 ? <Tag color="green">正常</Tag> : <Tag color="red">禁用</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label="最后登录">{user?.last_login_at || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{user?.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
