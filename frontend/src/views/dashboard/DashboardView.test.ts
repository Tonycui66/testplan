import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DashboardView from './DashboardView.vue'

describe('DashboardView', () => {
  it('renders the current version', () => {
    const wrapper = mount(DashboardView)
    expect(wrapper.text()).toContain('0.1.0-alpha')
  })
})
