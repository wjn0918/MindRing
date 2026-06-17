const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    keyword: '',
    concepts: [],
    newConceptName: '',
    newConceptDescription: '',
    loading: false,
    creating: false,
    user: null,
    isLoggedIn: false,
    showPrivacy: !wx.getStorageSync('mindring_privacy_accepted'),
    showSearch: false,
    showCreate: false
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

  goToLogin() {
    wx.switchTab({ url: '/pages/login/login' })
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/login/login' })
  },

  // 搜索弹窗
  openSearch() {
    this.setData({ showSearch: true })
  },

  closeSearch() {
    this.setData({ showSearch: false })
  },

  doSearch() {
    this.closeSearch()
    this.loadConcepts()
  },

  // 创建弹窗
  openCreate() {
    if (!this.data.isLoggedIn) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      wx.switchTab({ url: '/pages/login/login' })
      return
    }
    this.setData({ showCreate: true })
  },

  closeCreate() {
    this.setData({ showCreate: false })
  },

  stopPropagation() {
    // 阻止事件冒泡
  },

  onKeywordInput(event) {
    this.setData({ keyword: event.detail.value })
  },

  onConceptNameInput(event) {
    this.setData({ newConceptName: event.detail.value })
  },

  onConceptDescriptionInput(event) {
    this.setData({ newConceptDescription: event.detail.value })
  },

  acceptPrivacy() {
    wx.setStorageSync('mindring_privacy_accepted', true)
    this.setData({ showPrivacy: false })
  },

  loadConcepts() {
    if (!this.data.isLoggedIn) {
      this.setData({ loading: false, concepts: [] })
      return
    }
    this.setData({ loading: true })
    request('/concepts', {
      query: {
        q: this.data.keyword
      }
    })
      .then((concepts) => {
        this.setData({ concepts })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ loading: false }))
  },

  createConcept() {
    const name = this.data.newConceptName.trim()
    if (!name) {
      wx.showToast({ title: '先写下概念名称', icon: 'none' })
      return
    }

    this.setData({ creating: true })
    request('/concepts', {
      method: 'POST',
      data: {
        name,
        description: this.data.newConceptDescription.trim()
      }
    })
      .then((concept) => {
        this.setData({ 
          newConceptName: '', 
          newConceptDescription: '',
          showCreate: false
        })
        wx.navigateTo({ url: `/pages/concept/concept?id=${concept.id}` })       
      })
      .catch((error) => {
        wx.showToast({ title: error.message, icon: 'none' })
      })
      .finally(() => this.setData({ creating: false }))
  },

  openConcept(event) {
    wx.navigateTo({ url: `/pages/concept/concept?id=${event.currentTarget.dataset.id}` })
  }
})
