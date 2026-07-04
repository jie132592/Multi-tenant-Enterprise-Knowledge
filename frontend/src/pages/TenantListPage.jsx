import { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { tenantAPI } from '../api';

export default function TenantListPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTenant, setEditingTenant] = useState(null);
  const [form] = Form.useForm();

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const res = await tenantAPI.list({ page: 1, page_size: 100 });
      if (res.code === 200) {
        setData(res.data || []);
      }
    } catch (err) {
      message.error('获取租户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenants();
  }, []);

  const handleAdd = () => {
    setEditingTenant(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingTenant(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      const res = await tenantAPI.delete(id);
      if (res.code === 200) {
        message.success('删除成功');
        fetchTenants();
      }
    } catch (err) {
      message.error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingTenant) {
        const res = await tenantAPI.update(editingTenant.id, values);
        if (res.code === 200) {
          message.success('更新成功');
        }
      } else {
        const res = await tenantAPI.create(values);
        if (res.code === 200) {
          message.success('创建成功');
        }
      }
      setModalVisible(false);
      fetchTenants();
    } catch (err) {
      if (err.errorFields) return;
      message.error(err.response?.data?.detail || '操作失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '名称', dataIndex: 'name' },
    { title: '编码', dataIndex: 'code' },
    { title: '状态', dataIndex: 'status', render: (v) => v === 1 ? '正常' : '禁用' },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    { title: '用户数', dataIndex: 'user_count', width: 100 },
    { title: '知识库数', dataIndex: 'kb_count', width: 100 },
    {
      title: '操作',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, margin: 0 }}>租户管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新建租户</Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 20 }}
      />

      <Modal
        title={editingTenant ? '编辑租户' : '新建租户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="租户名称" rules={[{ required: true, message: '请输入租户名称' }]}>
            <Input placeholder="请输入租户名称" />
          </Form.Item>
          <Form.Item
            name="code"
            label="租户编码"
            rules={[
              { required: true, message: '请输入租户编码' },
              { pattern: /^[a-z0-9_]+$/, message: '只能包含小写字母、数字和下划线' }
            ]}
          >
            <Input placeholder="请输入租户编码" disabled={!!editingTenant} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          {editingTenant && (
            <Form.Item name="status" label="状态">
              <Input type="number" placeholder="1=正常, 0=禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
