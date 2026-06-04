const { request } = require('../../utils/api')
const app = getApp()

function today() {
  const date = new Date()
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

Page({
  data: {
    conceptId: null,
    insightId: null,
    isEditing: false,
    content: '',
    mood: '',
    tagText: '',
    occurredDate: today(),
    isShared: false,
    submitting: false
  },

  onLoad(options) {
    if (options.insightId) {
      this.setData({ 
        insightId: Number(options.insightId), 
        isEditing: true 
      })
      this.loadInsight()
    } else if (options.conceptId) {
      this.setData({ conceptId: Number(options.conceptId) })
    }
  },

  loadInsight() {
    wx.showLoading({ title: '加载中…' })
    request(`/insights/${this.data.insightId}`)
      .then((insight) => {
        const date = new Date(insight.occurred_at)
        const year = date.getFullYear()
        const month = `${date.getMonth() + 1}`.padStart(2, '0')
        const day = `${date.getDate()}`.padStart(2, '0')
        this.setData({
          conceptId: insight.concept_id,
          content: insight.content,
          mood: insight.mood || '',
          tagText: (insight.tags || []).join('，'),
          occurredDate: `${year}-${month}-${day}`,
          isShared: insight.is_shared
        })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => wx.hideLoading())
  },

  onContentInput(event) {
    this.setData({ content: event.detail.value })
  },

  onMoodInput(event) {
    this.setData({ mood: event.detail.value })
  },

  onTagsInput(event) {
    this.setData({ tagText: event.detail.value })
  },

  onDateChange(event) {
    this.setData({ occurredDate: event.detail.value })
  },

  onSharedChange(event) {
    this.setData({ isShared: event.detail.value })
  },

  submitInsight() {
    const content = this.data.content.trim()
    if (!content) {
      wx.showToast({ title: '先写下此刻的理解', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    const data = {
      content,
      mood: this.data.mood.trim(),
      tags: this.data.tagText
        .split(/[,，]/)
        .map((tag) => tag.trim())
        .filter((tag) => tag),
      is_shared: this.data.isShared,
      occurred_at: `${this.data.occurredDate}T12:00:00+00:00`
    }

    if (this.data.isEditing) {
      request(`/insights/${this.data.insightId}`, {
        method: 'PATCH',
        data
      })
        .then(() => {
          wx.showToast({ title: '更新成功', icon: 'success' })
          setTimeout(() => wx.navigateBack(), 500)
        })
        .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
        .finally(() => this.setData({ submitting: false }))
    } else {
      request('/insights', {
        method: 'POST',
        data: {
          concept_id: this.data.conceptId,
          ...data
        }
      })
        .then(() => {
          wx.showToast({ title: '已留下微光', icon: 'success' })
          setTimeout(() => wx.navigateBack(), 500)
        })
        .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
        .finally(() => this.setData({ submitting: false }))
    }
  }
})
