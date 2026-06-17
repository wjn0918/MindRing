const { request } = require('../../utils/api')
const app = getApp()

function formatDate(value) {
  const date = new Date(value)
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}.${month}.${day}`
}

function calculateAge(birthDate, targetDate) {
  if (!birthDate) return null
  const birth = new Date(birthDate)
  const target = new Date(targetDate)
  
  let age = target.getFullYear() - birth.getFullYear()
  const monthDiff = target.getMonth() - birth.getMonth()
  
  if (monthDiff < 0 || (monthDiff === 0 && target.getDate() < birth.getDate())) {
    age--
  }
  
  return age
}

Page({
  data: {
    conceptId: null,
    concept: {},
    insights: [],
    ringCircles: [64, 98, 132, 166, 200],
    loading: false,
    canManage: false,
    onlyMine: true,
    user: null,
    isLoggedIn: false
  },

  onLoad(options) {
    this.setData({ conceptId: Number(options.id) })
  },

  onShow() {
    this.checkLoginStatus()
    if (this.data.conceptId) {
      this.loadConcept()
      this.loadTimeline()
    }
  },

  checkLoginStatus() {
    const user = app.globalData.user
    const isLoggedIn = app.isLoggedIn()
    this.setData({ user, isLoggedIn })
  },

  loadConcept() {
    request(`/concepts/${this.data.conceptId}`)
      .then((concept) => {
        const user = app.globalData.user
        const canManage = user && concept.creator_id === user.id
        this.setData({ concept, canManage })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
  },

  loadTimeline() {
    this.setData({ loading: true })
    const user = app.globalData.user
    request(`/concepts/${this.data.conceptId}/timeline`, {
      query: { 
        order: 'desc', 
        only_mine: this.data.onlyMine
      }
    })
      .then((insights) => {
        const mapped = insights.map((insight) => {
          let age = null
          if (user && user.birth_date && 
              user.id === insight.author_id) {
            age = calculateAge(user.birth_date, insight.occurred_at)
          }
          return {
            ...insight,
            dateLabel: formatDate(insight.occurred_at),
            age: age
          }
        })
        const circles = [64, 98, 132, 166, 200, 234]
          .slice(0, Math.max(3, Math.min(6, mapped.length + 2)))
        this.setData({ insights: mapped, ringCircles: circles })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ loading: false }))
  },

  onFilterChange(e) {
    this.setData({ onlyMine: e.detail.value }, () => {
      this.loadTimeline()
    })
  },

  addInsight() {
    if (!app.requireLogin()) {
      return
    }
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

    request('/share-posters', {
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

  showActionMenu(e) {
    const insight = e.currentTarget.dataset.insight
    const that = this
    const itemList = []
    itemList.push(insight.is_shared ? '取消共享' : '共享')
    itemList.push('编辑')
    itemList.push('删除')
    
    wx.showActionSheet({
      itemList,
      success(res) {
        if (res.tapIndex === 0) {
          // 切换共享
          that.toggleShare(insight)
        } else if (res.tapIndex === 1) {
          // 编辑
          wx.navigateTo({ url: `/pages/insight/insight?insightId=${insight.id}` })
        } else if (res.tapIndex === 2) {
          // 删除
          that.deleteInsight(insight)
        }
      }
    })
  },

  toggleShare(insight) {
    wx.showLoading({ title: '处理中…' })
    request(`/insights/${insight.id}`, {
      method: 'PATCH',
      data: { is_shared: !insight.is_shared }
    })
      .then(() => {
        wx.showToast({ 
          title: insight.is_shared ? '已取消共享' : '已共享', 
          icon: 'success' 
        })
        this.loadTimeline()
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => wx.hideLoading())
  },

  deleteInsight(insight) {
    const that = this
    wx.showModal({
      title: '删除理解',
      content: '确定要删除这一次理解吗？删除后无法恢复。',
      confirmColor: '#ff4444',
      success(res) {
        if (res.confirm) {
          wx.showLoading({ title: '删除中…' })
          request(`/insights/${insight.id}`, {
            method: 'DELETE'
          })
            .then(() => {
              wx.showToast({ title: '删除成功', icon: 'success' })
              setTimeout(() => wx.hideLoading(), 500)
              setTimeout(() => {
                // 刷新时间轴
                that.loadTimeline()
              }, 600)
            })
            .catch((error) => {
              wx.hideLoading()
              wx.showToast({ title: error.message, icon: 'none' })
            })
        }
      }
    })
  },

  onShareAppMessage() {
    return {
      title: `我正在生长「${this.data.concept.name || '一个概念'}」的认知年轮`,
      path: `/pages/concept/concept?id=${this.data.conceptId}`
    }
  }
})
