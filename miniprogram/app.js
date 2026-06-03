App({
  globalData: {
    token: wx.getStorageSync('mindring_token') || '',
    user: null,
    apiBase: '' // 动态设置
  },

  onLaunch() {
    this.initEnv()
    this.checkAuth()
  },

  initEnv() {
    // 获取当前小程序运行环境
    const accountInfo = wx.getAccountInfoSync()
    const env = accountInfo.miniProgram.envVersion

    // 根据环境设置 apiBase
    const baseUrls = {
      develop: 'https://mapi.catpd.cn/api', // 开发版
      trial: 'https://mapi.catpd.cn/api', // 体验版
      release: 'https://mapi.catpd.cn/api' // 正式版
    }

    this.globalData.apiBase = baseUrls[env] || baseUrls.develop
    console.log('Current API Base:', this.globalData.apiBase)
  },

  checkAuth() {
    const token = wx.getStorageSync('mindring_token')
    const user = wx.getStorageSync('mindring_user')
    if (token && user) {
      this.globalData.token = token
      this.globalData.user = user
    }
  },

  isLoggedIn() {
    const token = this.globalData.token || wx.getStorageSync('mindring_token') || ''
    this.globalData.token = token
    return !!token
  },

  setAuth(token, user) {
    this.globalData.token = token
    this.globalData.user = user
    wx.setStorageSync('mindring_token', token)
    wx.setStorageSync('mindring_user', user)
  },

  clearAuth() {
    this.globalData.token = ''
    this.globalData.user = null
    wx.removeStorageSync('mindring_token')
    wx.removeStorageSync('mindring_user')
  },

  requireLogin(message = '请先登录后再继续操作。') {
    if (this.isLoggedIn()) return true

    wx.showModal({
      title: '登录后可用',
      content: message,
      showCancel: false,
      success: () => {
        wx.switchTab({ url: '/pages/login/login' })
      }
    })
    return false
  }
})
