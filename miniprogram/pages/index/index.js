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
    showPrivacy: !wx.getStorageSync('mindring_privacy_accepted')
  },

  onShow() {
    this.loadConcepts()
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
        this.setData({ newConceptName: '', newConceptDescription: '', newConceptShared: false })
        wx.navigateTo({ url: `/pages/concept/concept?id=${concept.id}` })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ creating: false }))
  },

  openConcept(event) {
    wx.navigateTo({ url: `/pages/concept/concept?id=${event.currentTarget.dataset.id}` })
  }
})
