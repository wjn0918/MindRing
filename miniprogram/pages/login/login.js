const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    user: app.globalData.user,
    loading: false,
    isLoggedIn: false
  },

  onLoad() {
    this.checkLoginStatus()
  },

  onShow() {
    this.checkLoginStatus()
  },

  checkLoginStatus() {
    const user = app.globalData.user
    const isLoggedIn = user && user.id !== 'demo_user'
    this.setData({ user, isLoggedIn })
  },

  loginWithWechat() {
    this.setData({ loading: true })
    
    // 第一步：使用 wx.getUserProfile 获取用户信息（需要用户主动授权）
    wx.getUserProfile({
      desc: '用于完善会员资料',
      success: (profileResult) => {
        const userInfo = profileResult.userInfo
        
        // 第二步：获取登录 code
        wx.login({
          success: (loginResult) => {
            // 第三步：将 code 和用户信息一起发送给后端
            request('/api/wechat/login', {
              method: 'POST',
              data: { 
                code: loginResult.code,
                nickname: userInfo.nickName,
                avatar_url: userInfo.avatarUrl
              }
            })
              .then((profile) => {
                const user = {
                  id: profile.openid,
                  nickname: profile.nickname || userInfo.nickName || '微光旅人',
                  avatarUrl: profile.avatar_url || userInfo.avatarUrl || ''
                }
                app.setUser(user)
                this.setData({ user, isLoggedIn: true, loading: false })
                wx.showToast({ title: '登录成功', icon: 'success' })
                setTimeout(() => {
                  wx.switchTab({ url: '/pages/index/index' })
                }, 1500)
              })
              .catch((error) => {
                this.setData({ loading: false })
                wx.showToast({ title: error.message, icon: 'none' })
              })
          },
          fail: () => {
            this.setData({ loading: false })
            wx.showToast({ title: '微信登录失败', icon: 'none' })
          }
        })
      },
      fail: (err) => {
        this.setData({ loading: false })
        console.error('获取用户信息失败', err)
        wx.showToast({ title: '需要授权才能登录', icon: 'none' })
      }
    })
  },

  loginAnonymously() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          const guestUser = {
            id: 'demo_user',
            nickname: '微光旅人',
            avatarUrl: ''
          }
          app.setUser(guestUser)
          this.setData({ user: guestUser, isLoggedIn: false })
          wx.removeStorageSync('mindring_user')
          wx.showToast({ title: '已退出', icon: 'success' })
        }
      }
    })
  }
})
