<template>
  <div class="role-list-page">
    <div class="page-header">
      <h2>角色权限说明</h2>
    </div>

    <el-table :data="roleList" v-loading="loading" stripe>
      <el-table-column prop="name" label="角色" width="150">
        <template #default="{ row }">
          <el-tag :type="row.tagType" size="large">{{ row.label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="说明" min-width="200" />
      <el-table-column prop="permissions" label="权限" min-width="400">
        <template #default="{ row }">
          <div class="permissions-wrap">
            <el-tag
              v-for="perm in row.permissions"
              :key="perm"
              size="small"
              class="perm-tag"
            >
              {{ perm }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="tips">
      <el-alert type="info" :closable="false">
        <template #title>
          <strong>说明：</strong>角色是系统预定义的，不可创建或修改。用户权限通过分配角色来控制。
          角色的分配在"用户管理"页面中进行。
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const loading = ref(false)

const roleList = ref([
  {
    name: 'super_admin',
    label: '超级管理员',
    tagType: 'danger',
    description: '系统级管理员，可管理所有租户和全局设置',
    permissions: ['kb:manage', 'kb:create', 'kb:delete', 'doc:upload', 'doc:delete', 'dept:manage', 'user:manage']
  },
  {
    name: 'tenant_admin',
    label: '租户管理员',
    tagType: 'warning',
    description: '租户内管理员，可管理本租户内的所有资源',
    permissions: ['kb:manage', 'kb:create', 'kb:delete', 'doc:upload', 'doc:delete', 'dept:manage', 'user:manage']
  },
  {
    name: 'member',
    label: '普通成员',
    tagType: 'success',
    description: '普通用户，只能创建知识库和上传文档',
    permissions: ['kb:create', 'doc:upload']
  }
])
</script>

<style lang="scss" scoped>
.role-list-page {
  .page-header {
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 18px;
      color: #333;
    }
  }

  .permissions-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .perm-tag {
    font-family: monospace;
  }

  .tips {
    margin-top: 20px;
  }
}
</style>
