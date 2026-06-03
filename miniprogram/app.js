App({
  globalData: {
    apiBaseUrl: 'http://127.0.0.1:8000',
    user: null
  },

  onLaunch() {
    this.checkAuth()
  },

  checkAuth() {
    const token = wx.getStorageSync('mindring_token')
    const user = wx.getStorageSync('mindring_user')
    if (token && user) {
      this.globalData.user = user
    }
  },

  setAuth(token, user) {
    this.globalData.user = user
    wx.setStorageSync('mindring_token', token)
    wx.setStorageSync('mindring_user', user)
  },

  clearAuth() {
    this.globalData.user = null
    wx.removeStorageSync('mindring_token')
    wx.removeStorageSync('mindring_user')
  }
})
