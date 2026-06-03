const { request } = require('../../utils/api')

function formatDate(value) {
  const date = new Date(value)
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}.${month}.${day}`
}

Page({
  data: {
    conceptId: null,
    concept: {},
    insights: [],
    ringCircles: [64, 98, 132, 166, 200],
    loading: false
  },

  onLoad(options) {
    this.setData({ conceptId: Number(options.id) })
  },

  onShow() {
    if (this.data.conceptId) {
      this.loadConcept()
      this.loadTimeline()
    }
  },

  loadConcept() {
    request(`/api/concepts/${this.data.conceptId}`)
      .then((concept) => this.setData({ concept }))
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
  },

  loadTimeline() {
    this.setData({ loading: true })
    request(`/api/concepts/${this.data.conceptId}/timeline`, { query: { order: 'desc' } })
      .then((insights) => {
        const mapped = insights.map((insight) => ({
          ...insight,
          dateLabel: formatDate(insight.occurred_at)
        }))
        const circles = [64, 98, 132, 166, 200, 234]
          .slice(0, Math.max(3, Math.min(6, mapped.length + 2)))
        this.setData({ insights: mapped, ringCircles: circles })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ loading: false }))
  },

  addInsight() {
    wx.navigateTo({ url: `/pages/insight/insight?conceptId=${this.data.conceptId}` })
  },

  openDiff() {
    wx.navigateTo({ url: `/pages/diff/diff?conceptId=${this.data.conceptId}` })
  },

  createPoster() {
    const latest = this.data.insights[0]
    if (!latest) {
      wx.showToast({ title: '还没有可分享的理解', icon: 'none' })
      return
    }

    request('/api/share-posters', {
      method: 'POST',
      data: {
        concept_name: this.data.concept.name,
        insight_content: latest.content,
        time_span: latest.dateLabel
      }
    })
      .then((poster) => {
        wx.setClipboardData({
          data: `${poster.title}\n${poster.subtitle}\n${poster.content}`,
          success: () => wx.showToast({ title: '海报文案已复制', icon: 'success' })
        })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
  },

  onShareAppMessage() {
    return {
      title: `我正在生长「${this.data.concept.name || '一个概念'}」的认知年轮`,
      path: `/pages/concept/concept?id=${this.data.conceptId}`
    }
  }
})
