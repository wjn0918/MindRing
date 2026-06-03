App({
  globalData: {
    apiBaseUrl: 'http://127.0.0.1:8000',
    user: {
      id: 'demo_user',
      nickname: '微光旅人',
      avatarUrl: ''
    }
  },

  onLaunch() {
    const storedUser = wx.getStorageSync('mindring_user')
    if (storedUser && storedUser.id) {
      this.globalData.user = storedUser
    }
  },

  setUser(user) {
    this.globalData.user = user
    wx.setStorageSync('mindring_user', user)
  }
})
