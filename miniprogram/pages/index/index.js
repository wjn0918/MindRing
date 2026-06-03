const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    keyword: '',
    concepts: [],
    newConceptName: '',
    newConceptDescription: '',
    newConceptShared: false,
    loading: false,
    creating: false,
    user: app.globalData.user,
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
    const isLoggedIn = user && user.id !== 'demo_user'
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

  onConceptSharedChange(event) {
    this.setData({ newConceptShared: event.detail.value })
  },

  acceptPrivacy() {
    wx.setStorageSync('mindring_privacy_accepted', true)
    this.setData({ showPrivacy: false })
  },

  loginWithWechat() {
    wx.login({
      success: (loginResult) => {
        request('/api/wechat/login', {
          method: 'POST',
          data: { code: loginResult.code }
        })
          .then((profile) => {
            const user = {
              id: profile.openid,
              nickname: profile.nickname || this.data.user.nickname || '微光旅人',
              avatarUrl: profile.avatar_url || ''
            }
            app.setUser(user)
            this.setData({ user })
            this.loadConcepts()
            wx.showToast({ title: '已登录', icon: 'success' })
          })
          .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      },
      fail: () => wx.showToast({ title: '微信登录失败', icon: 'none' })
    })
  },

  loadConcepts() {
    this.setData({ loading: true })
    request('/api/concepts', {
      query: {
        q: this.data.keyword,
        viewer_id: app.globalData.user.id
      }
    })
      .then((concepts) => {
        const mapped = concepts.map((concept) => ({
          ...concept,
          visibilityLabel: concept.is_shared ? '共享' : '私密'
        }))
        this.setData({ concepts: mapped })
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
    request('/api/concepts', {
      method: 'POST',
      data: {
        name,
        description: this.data.newConceptDescription.trim(),
        creator_id: app.globalData.user.id,
        is_shared: this.data.newConceptShared
      }
    })
      .then((concept) => {
        this.setData({ 
          newConceptName: '', 
          newConceptDescription: '', 
          newConceptShared: false,
          showCreate: false
        })
        wx.navigateTo({ url: `/pages/concept/concept?id=${concept.id}` })       
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))   
      .finally(() => this.setData({ creating: false }))
  },

  openConcept(event) {
    wx.navigateTo({ url: `/pages/concept/concept?id=${event.currentTarget.dataset.id}` })
  }
})