const { request } = require('../../utils/api')

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
    content: '',
    mood: '',
    tagText: '',
    occurredDate: today(),
    isShared: false,
    submitting: false
  },

  onLoad(options) {
    this.setData({ conceptId: Number(options.conceptId) })
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
    request('/insights', {
      method: 'POST',
      data: {
        concept_id: this.data.conceptId,
        content,
        mood: this.data.mood.trim(),
        tags: this.data.tagText
          .split(/[,，]/)
          .map((tag) => tag.trim())
          .filter((tag) => tag),
        is_shared: this.data.isShared,
        occurred_at: `${this.data.occurredDate}T12:00:00+00:00`
      }
    })
      .then(() => {
        wx.showToast({ title: '已留下微光', icon: 'success' })
        setTimeout(() => wx.navigateBack(), 500)
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ submitting: false }))
  }
})
