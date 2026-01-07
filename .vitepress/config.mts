import { defineConfig } from 'vitepress'
import { generateSidebar } from 'vitepress-sidebar'

function processItems(items, depth = 1) {
  items.forEach(item => {
    if (item.items) {
      item.collapsed = depth >= 2
      processItems(item.items, depth + 1)
    }

    if (item.link) {
      if (!item.link.startsWith('/tutorials/')) {
        const cleanLink = item.link.replace(/^\//, '')
        item.link = `/tutorials/${cleanLink}`
      }
    }
  })

  items.sort((a, b) => {
    const isFolderA = !!a.items
    const isFolderB = !!b.items

    if (isFolderA && !isFolderB) return -1
    if (!isFolderA && isFolderB) return 1
    return 0
  })
}

function customizeSidebar(sidebar) {
  processItems(sidebar)
  return sidebar
}

const rawSidebar = generateSidebar({
  documentRootPath: '/',
  scanStartPath: 'tutorials',
  useTitleFromFileHeading: true,
  hyphenToSpace: true,
  underscoreToSpace: true,
  removePrefixAfterOrdering: true,
  prefixSeparator: '-', 
  collapsed: false,
  collapseDepth: 2
})

const finalSidebar = customizeSidebar(rawSidebar)

export default defineConfig({
 
  base: '/', 
  
  title: "Hi Hi Nasir",
  description: "用來記錄的 Nasir 小天地！",
  
  themeConfig: {
    externalLinkIcon: true, 
    
    nav: [
      { text: '首頁', link: '/' },
      { text: 'START', link: '/tutorials/intro' },
      { text: 'About Me', link: 'https://nasirlin.net' }
    ],

    sidebar: {
      '/tutorials/': finalSidebar
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/nasircy' },
      { icon: 'youtube', link: 'https://www.youtube.com/@jimmypiano' }
    ]
  }
})