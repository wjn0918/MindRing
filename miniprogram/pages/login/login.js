const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    user: null,
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
    const isLoggedIn = !!user
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
            request('/wechat/login', {
              method: 'POST',
              data: { 
                code: loginResult.code,
                nickname: userInfo.nickName,
                avatar_url: userInfo.avatarUrl
              }
            })
              .then((response) => {
                app.setAuth(response.access_token, response.user)
                this.setData({ 
                  user: response.user, 
                  isLoggedIn: true, 
                  loading: false 
                })
                wx.showToast({ title: '登录成功', icon: 'success' })
                
                // 检查是否设置了出生年月
                if (!response.user.birth_date) {
                  setTimeout(() => {
                    wx.navigateTo({ url: '/pages/birthdate/birthdate' })
                  }, 1500)
                } else {
                  setTimeout(() => {
                    wx.switchTab({ url: '/pages/index/index' })
                  }, 1500)
                }
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

  goToSetBirthdate() {
    wx.navigateTo({ url: '/pages/birthdate/birthdate' })
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
          app.clearAuth()
          this.setData({ user: null, isLoggedIn: false })
          wx.showToast({ title: '已退出', icon: 'success' })
        }
      }
    })
  }
})
