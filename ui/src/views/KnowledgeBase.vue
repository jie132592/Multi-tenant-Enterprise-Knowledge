<template>
  <div class="knowledge-base-page">
    <div class="toolbar">
      <div class="left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索知识库..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
          @change="handleSearch"
        />
      </div>
      <div class="right">
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新建知识库
        </el-button>
      </div>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="200">
        <template #default="{ row }">
          <div class="name-cell">
            <span class="name">{{ row.name }}</span>
            <span v-if="row.description" class="desc">{{ row.description }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="visibility" label="可见性" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.visibility === 'public'" type="success" size="small">全员</el-tag>
          <el-tag v-else-if="row.visibility === 'department'" type="warning" size="small">部门</el-tag>
          <el-tag v-else type="info" size="small">私有</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="document_count" label="文档数" width="100" align="center" />
      <el-table-column prop="paragraph_count" label="段落数" width="100" align="center" />
      <el-table-column prop="creator_username" label="创建者" width="120" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="180" align="center">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="primary" link @click="handleDocuments(row)">文档</el-button>
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
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
        <el-form-item label="可见性" prop="visibility">
          <el-select v-model="form.visibility" placeholder="选择可见性" style="width: 100%">
            <el-option label="全员可见" value="public" />
            <el-option label="部门可见" value="department" />
            <el-option label="私有（仅自己）" value="private" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.visibility === 'department'" label="部门" prop="department_id">
          <el-select
            v-model="form.department_id"
            placeholder="选择可见部门"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="dept in departmentList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { knowledgeApi, type KnowledgeBase } from '../api/knowledge'
import { departmentApi } from '../api/department'

const router = useRouter()

const loading = ref(false)
const tableData = ref<KnowledgeBase[]>([])
const departmentList = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('新建知识库')
const submitting = ref(false)
const editingId = ref<number | null>(null)

const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  description: '',
  visibility: 'private',
  department_id: undefined as number | undefined
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }]
}

const loadDepartmentList = async () => {
  try {
    const data = await departmentApi.list()
    departmentList.value = data || []
  } catch (error) {
    console.error(error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const data = await knowledgeApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined
    })
    tableData.value = data || []
    total.value = tableData.value.length
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
  dialogTitle.value = '新建知识库'
  editingId.value = null
  form.name = ''
  form.description = ''
  form.visibility = 'private'
  form.department_id = undefined
  dialogVisible.value = true
}

const handleEdit = (row: KnowledgeBase) => {
  dialogTitle.value = '编辑知识库'
  editingId.value = row.id
  form.name = row.name
  form.description = row.description
  form.visibility = row.visibility || 'private'
  form.department_id = row.department_id
  dialogVisible.value = true
}

const handleDocuments = (row: KnowledgeBase) => {
  router.push(`/kb/${row.id}/documents`)
}

const handleDelete = async (row: KnowledgeBase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库「${row.name}」吗？删除后无法恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await knowledgeApi.delete(row.id)
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
          await knowledgeApi.update(editingId.value, {
            name: form.name,
            description: form.description,
            visibility: form.visibility,
            department_id: form.department_id
          })
          ElMessage.success('更新成功')
        } else {
          await knowledgeApi.create({
            name: form.name,
            description: form.description,
            visibility: form.visibility,
            department_id: form.department_id
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
  loadDepartmentList()
})
</script>

<style lang="scss" scoped>
.knowledge-base-page {
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
