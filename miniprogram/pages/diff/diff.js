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
    insights: [],
    insightLabels: [],
    leftIndex: 1,
    rightIndex: 0,
    diff: null,
    loadingDiff: false
  },

  onLoad(options) {
    this.setData({ conceptId: Number(options.conceptId) })
    this.loadInsights()
  },

  loadInsights() {
    request(`/api/concepts/${this.data.conceptId}/insights`, {
      query: { order: 'desc' }
    })
      .then((insights) => {
        const labels = insights.map((insight) => `${formatDate(insight.occurred_at)} · ${insight.mood || '未标注心境'}`)
        this.setData({ insights, insightLabels: labels, leftIndex: Math.min(1, insights.length - 1) })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
  },

  onLeftChange(event) {
    this.setData({ leftIndex: Number(event.detail.value), diff: null })
  },

  onRightChange(event) {
    this.setData({ rightIndex: Number(event.detail.value), diff: null })
  },

  loadDiff() {
    const left = this.data.insights[this.data.leftIndex]
    const right = this.data.insights[this.data.rightIndex]
    if (!left || !right) {
      wx.showToast({ title: '请选择两条理解', icon: 'none' })
      return
    }
    if (left.id === right.id) {
      wx.showToast({ title: '请选择不同时间点', icon: 'none' })
      return
    }

    this.setData({ loadingDiff: true })
    request('/api/insights/diff', {
      query: { left_id: left.id, right_id: right.id }
    })
      .then((diff) => this.setData({ diff }))
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ loadingDiff: false }))
  }
})
