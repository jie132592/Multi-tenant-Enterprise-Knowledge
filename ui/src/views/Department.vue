<template>
  <div class="department-page">
    <div class="toolbar">
      <div class="left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索部门..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
          @change="handleSearch"
        />
      </div>
      <div class="right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建部门
        </el-button>
      </div>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="部门名称" min-width="200">
        <template #default="{ row }">
          <div class="name-cell">
            <span class="name">{{ row.name }}</span>
            <span v-if="row.description" class="desc">{{ row.description }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="code" label="部门编码" width="150" />
      <el-table-column prop="leader_username" label="负责人" width="120" align="center">
        <template #default="{ row }">
          {{ row.leader_username || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="user_count" label="成员数" width="100" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="180" align="center">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入部门编码（唯一）" />
        </el-form-item>
        <el-form-item label="上级部门" prop="parent_id">
          <el-select
            v-model="form.parent_id"
            placeholder="选择上级部门（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="dept in allDepartments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
              :disabled="dept.id === editingId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述（可选）"
          />
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
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { departmentApi, type Department } from '../api/department'

const loading = ref(false)
const tableData = ref<Department[]>([])
const allDepartments = ref<Department[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('新建部门')
const submitting = ref(false)
const editingId = ref<number | null>(null)

const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  code: '',
  parent_id: undefined as number | undefined,
  description: ''
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入部门编码', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const data = await departmentApi.list({
      keyword: searchKeyword.value || undefined
    })
    tableData.value = data || []
    total.value = tableData.value.length
    allDepartments.value = data || []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
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

const handleCreate = () => {
  dialogTitle.value = '新建部门'
  editingId.value = null
  form.name = ''
  form.code = ''
  form.parent_id = undefined
  form.description = ''
  dialogVisible.value = true
}

const handleEdit = (row: Department) => {
  dialogTitle.value = '编辑部门'
  editingId.value = row.id
  form.name = row.name
  form.code = row.code
  form.parent_id = row.parent_id
  form.description = row.description || ''
  dialogVisible.value = true
}

const handleDelete = async (row: Department) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部门「${row.name}」吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await departmentApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (editingId.value) {
          await departmentApi.update(editingId.value, {
            name: form.name,
            code: form.code,
            parent_id: form.parent_id,
            description: form.description
          })
          ElMessage.success('更新成功')
        } else {
          await departmentApi.create({
            name: form.name,
            code: form.code,
            parent_id: form.parent_id,
            description: form.description
          })
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
      } catch (error) {
        console.error(error)
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.department-page {
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .name-cell {
    display: flex;
    flex-direction: column;

    .name {
      font-weight: 500;
    }

    .desc {
      font-size: 12px;
      color: #999;
      margin-top: 4px;
    }
  }

  .pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
