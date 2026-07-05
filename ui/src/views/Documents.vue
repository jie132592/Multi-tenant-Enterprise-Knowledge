<template>
  <div class="documents-page">
    <div class="toolbar">
      <div class="left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <span class="kb-name">{{ kbName }}</span>
      </div>
      <div class="right">
        <el-upload
          ref="uploadRef"
          :http-request="handleUpload"
          :show-file-list="false"
          accept=".txt,.md,.pdf"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </el-upload>
      </div>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="文档名称" min-width="300">
        <template #default="{ row }">
          <div class="name-cell">
            <span class="name">{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="char_length" label="字符数" width="100" align="center">
        <template #default="{ row }">
          {{ row.char_length.toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="paragraph_count" label="段落数" width="100" align="center">
        <template #default="{ row }">
          {{ row.paragraph_count }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.status === 0" type="info">待处理</el-tag>
          <el-tag v-else-if="row.status === 1" type="warning">处理中</el-tag>
          <el-tag v-else-if="row.status === 2" type="success">已完成</el-tag>
          <el-tag v-else-if="row.status === 3" type="danger">失败</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="uploader_username" label="上传者" width="100" align="center" />
      <el-table-column prop="created_at" label="上传时间" width="180" align="center">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleView(row)">查看</el-button>
          <el-button
            v-if="row.status !== 2"
            type="warning"
            link
            :loading="row.parsing"
            @click="handleParse(row)"
          >
            解析
          </el-button>
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

    <!-- 文档内容弹窗 -->
    <el-dialog v-model="contentVisible" :title="currentDoc?.name" width="800px">
      <div v-if="contentLoading" style="text-align: center; padding: 40px">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>
      <div v-else-if="docContent" class="content-preview">
        <div class="content-header">
          <span>字符数：{{ docContent.char_length.toLocaleString() }}</span>
        </div>
        <el-input
          v-model="docContent.content"
          type="textarea"
          :rows="20"
          readonly
          class="content-textarea"
        />
      </div>
      <template #footer>
        <el-button @click="contentVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, ArrowLeft, Loading } from '@element-plus/icons-vue'
import { documentApi, type Document } from '../api/document'
import { knowledgeApi } from '../api/knowledge'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const uploading = ref(false)
const contentLoading = ref(false)
const tableData = ref<Document[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const kbId = ref<number>(0)
const kbName = ref('')

const contentVisible = ref(false)
const currentDoc = ref<Document | null>(null)
const docContent = ref<{ content: string; char_length: number } | null>(null)

const uploadRef = ref()

const loadKbInfo = async () => {
  try {
    const kb = await knowledgeApi.get(kbId.value)
    kbName.value = kb.name
  } catch (error) {
    console.error(error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const data = await documentApi.list(kbId.value, {
      page: currentPage.value,
      page_size: pageSize.value
    })
    tableData.value = (data || []).map((d: Document) => ({ ...d, parsing: false }))
    total.value = tableData.value.length
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleUpload = async (options: any) => {
  const { file } = options
  uploading.value = true
  try {
    await documentApi.upload(kbId.value, file)
    ElMessage.success('上传成功，正在解析...')
    // 刷新列表
    setTimeout(() => loadData(), 1000)
  } catch (error) {
    console.error(error)
  } finally {
    uploading.value = false
  }
}

const handleView = async (row: Document) => {
  currentDoc.value = row
  contentVisible.value = true
  contentLoading.value = true
  try {
    docContent.value = await documentApi.getContent(row.id)
  } catch (error) {
    console.error(error)
    ElMessage.error('加载内容失败')
  } finally {
    contentLoading.value = false
  }
}

const handleParse = async (row: Document) => {
  try {
    await documentApi.parse(row.id)
    ElMessage.success('解析任务已启动')
    // 轮询检查状态
    pollStatus(row)
  } catch (error) {
    console.error(error)
  }
}

const pollStatus = (row: Document) => {
  const interval = setInterval(async () => {
    try {
      const doc = await documentApi.get(row.id)
      const index = tableData.value.findIndex(d => d.id === row.id)
      if (index !== -1) {
        tableData.value[index].status = doc.status
        if (doc.status === 2 || doc.status === 3) {
          clearInterval(interval)
          if (doc.status === 2) {
            ElMessage.success(`文档「${doc.name}」解析完成`)
          } else {
            ElMessage.error(`文档「${doc.name}」解析失败: ${doc.error_message}`)
          }
          loadData()
        }
      }
    } catch (error) {
      clearInterval(interval)
    }
  }, 2000)

  // 最多等5分钟
  setTimeout(() => clearInterval(interval), 300000)
}

const handleDelete = async (row: Document) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档「${row.name}」吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await documentApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const goBack = () => {
  router.push('/kb')
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  kbId.value = Number(route.params.kbId)
  loadKbInfo()
  loadData()
})
</script>

<style lang="scss" scoped>
.documents-page {
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .left {
      display: flex;
      align-items: center;
      gap: 12px;

      .kb-name {
        font-size: 16px;
        font-weight: 500;
        color: #333;
      }
    }
  }

  .name-cell {
    .name {
      font-weight: 500;
    }
  }

  .pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }

  .content-preview {
    .content-header {
      margin-bottom: 12px;
      color: #666;
      font-size: 14px;
    }

    .content-textarea {
      :deep(textarea) {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        line-height: 1.6;
      }
    }
  }
}
</style>
