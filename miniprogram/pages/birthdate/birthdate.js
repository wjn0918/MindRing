const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    birthDate: '',
    saving: false
  },

  onLoad(options) {
    const user = app.globalData.user
    if (user && user.birth_date) {
      this.setData({ birthDate: user.birth_date })
    }
  },

  onDateChange(event) {
    this.setData({ birthDate: event.detail.value })
  },

  async saveBirthDate() {
    if (!this.data.birthDate) {
      wx.showToast({ 
        title: '请选择你的出生年月', 
        icon: 'none' 
      })
      return
    }

    this.setData({ saving: true })
    try {
      const updatedUser = await request('/users/me', {
        method: 'PATCH',
        data: {
          birth_date: this.data.birthDate
        }
      })
      
      app.setAuth(app.globalData.token, updatedUser)
      
      wx.showToast({ 
        title: '保存成功', 
        icon: 'success' 
      })
      
      setTimeout(() => {
        wx.navigateBack()
      }, 1000)
    } catch (error) {
      wx.showToast({ 
        title: error.message || '保存失败', 
        icon: 'none' 
      })
    } finally {
      this.setData({ saving: false })
    }
  }
})
