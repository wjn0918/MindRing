const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    concepts: [],
    loading: false,
    keyword: '',
    user: null,
    isLoggedIn: false
  },

  onShow() {
    this.checkLoginStatus()
    this.loadConcepts()
  },

  checkLoginStatus() {
    const user = app.globalData.user
    const isLoggedIn = !!user
    this.setData({ user, isLoggedIn })
  },

  loadConcepts() {
    if (!this.data.isLoggedIn) {
      this.setData({ loading: false, concepts: [] })
      return
    }
    this.setData({ loading: true })
    request('/concepts/all', {
      query: { q: this.data.keyword }
    })
      .then((concepts) => {
        this.setData({ concepts })
      })
      .catch((error) => {
        wx.showToast({ title: error.message, icon: 'none' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  onKeywordInput(event) {
    this.setData({ keyword: event.detail.value })
  },

  onSearch() {
    this.loadConcepts()
  },

  openConcept(event) {
    wx.navigateTo({ 
      url: `/pages/concept/concept?id=${event.currentTarget.dataset.id}`
    })
  }
})
