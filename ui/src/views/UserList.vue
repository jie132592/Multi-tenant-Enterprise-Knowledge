<template>
  <div class="user-list-page">
    <div class="toolbar">
      <div class="left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名或邮箱..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
          @change="handleSearch"
        />
      </div>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" min-width="150">
        <template #default="{ row }">
          <div class="user-cell">
            <span class="username">{{ row.username }}</span>
            <span v-if="row.is_super_admin" class="tag admin">超级管理员</span>
            <span v-else-if="row.is_tenant_admin" class="tag tenant-admin">租户管理员</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="200" />
      <el-table-column prop="role" label="角色" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getRoleTagType(row.role)" size="small">
            {{ getRoleName(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="department_name" label="部门" width="150" align="center">
        <template #default="{ row }">
          {{ row.department_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login_at" label="最后登录" width="180" align="center">
        <template #default="{ row }">
          {{ formatDate(row.last_login_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" align="center">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑部门</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="编辑用户"
      width="400px"
    >
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input :value="editingUser?.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input :value="editingUser?.email" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" placeholder="选择角色" style="width: 100%">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="租户管理员" value="tenant_admin" />
            <el-option label="普通成员" value="member" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="form.department_id" placeholder="选择部门" clearable style="width: 100%">
            <el-option
              v-for="dept in departmentList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User } from '../api/user'
import { userApi } from '../api/user'
import { departmentApi, type Department } from '../api/department'

const loading = ref(false)
const tableData = ref<User[]>([])
const departmentList = ref<Department[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

const dialogVisible = ref(false)
const submitting = ref(false)
const editingUser = ref<User | null>(null)

const form = reactive({
  role: 'member',
  department_id: undefined as number | undefined,
  is_active: 1
})

const loadData = async () => {
  loading.value = true
  try {
    const data = await userApi.list({
      keyword: searchKeyword.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    })
    tableData.value = data.list || []
    total.value = data.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadDepartmentList = async () => {
  try {
    const res = await departmentApi.list()
    if (res && Array.isArray(res)) {
      departmentList.value = res
    }
  } catch (error) {
    console.error(error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const handleEdit = (row: User) => {
  editingUser.value = row
  form.role = row.role || 'member'
  form.department_id = row.department_id || undefined
  form.is_active = row.is_active
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!editingUser.value) return

  submitting.value = true
  try {
    await userApi.update(editingUser.value.id, {
      role: form.role,
      department_id: form.department_id,
      is_active: form.is_active
    })
    ElMessage.success('更新成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getRoleName = (role: string) => {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    tenant_admin: '租户管理员',
    member: '普通成员'
  }
  return map[role] || role
}

const getRoleTagType = (role: string): '' | 'danger' | 'warning' | 'success' => {
  const map: Record<string, '' | 'danger' | 'warning' | 'success'> = {
    super_admin: 'danger',
    tenant_admin: 'warning',
    member: 'success'
  }
  return map[role] || ''
}

onMounted(() => {
  loadData()
  loadDepartmentList()
})
</script>

<style lang="scss" scoped>
.user-list-page {
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .user-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .username {
      font-weight: 500;
    }

    .tag {
      font-size: 12px;
      padding: 2px 6px;
      border-radius: 4px;

      &.admin {
        background: #f56c6c;
        color: #fff;
      }

      &.tenant-admin {
        background: #e6a23c;
        color: #fff;
      }
    }
  }

  .pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
