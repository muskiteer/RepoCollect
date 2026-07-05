// ─── Mobile nav toggle ───
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('mobile-toggle')
  const links = document.getElementById('nav-links')
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open')
    })
  }

  // Highlight active nav link
  const path = window.location.pathname.split('/').pop() || 'index.html'
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href')
    if (href === path || (path === '' && href === 'index.html')) {
      link.classList.add('active')
    }
  })

  // Close mobile nav on link click
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      links.classList.remove('open')
    })
  })

  // Endpoint accordion
  document.querySelectorAll('.endpoint-header').forEach(header => {
    header.addEventListener('click', () => {
      const body = header.nextElementSibling
      if (body) {
        body.classList.toggle('open')
      }
    })
  })

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'))
      if (target) {
        e.preventDefault()
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    })
  })

  // Theme toggle
  const themeBtn = document.getElementById('theme-toggle')
  if (themeBtn) {
    // Check saved preference or system preference
    if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.body.classList.add('dark-mode')
    }

    themeBtn.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode')
      if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark')
      } else {
        localStorage.setItem('theme', 'light')
      }
    })
  }
})
