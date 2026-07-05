document.addEventListener('DOMContentLoaded', () => {

  // ── Theme toggle ──
  const themeBtn = document.getElementById('theme-toggle')
  const body = document.body
  const saved = localStorage.getItem('theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  if (saved === 'dark' || (!saved && prefersDark)) body.classList.add('dark')

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      body.classList.toggle('dark')
      localStorage.setItem('theme', body.classList.contains('dark') ? 'dark' : 'light')
    })
  }

  // ── Sticky nav scroll shrink ──
  const nav = document.getElementById('nav')
  window.addEventListener('scroll', () => {
    if (window.scrollY > 60) {
      nav.style.borderBottomColor = 'var(--border)'
    } else {
      nav.style.borderBottomColor = 'transparent'
    }
  }, { passive: true })

  // ── Active nav link on scroll ──
  const sections = document.querySelectorAll('section[id], footer[id]')
  const navLinks = document.querySelectorAll('.nav-link')

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.classList.remove('active')
          if (link.getAttribute('href') === '#' + entry.target.id) {
            link.classList.add('active')
          }
        })
      }
    })
  }, { rootMargin: '-40% 0px -55% 0px' })

  sections.forEach(s => observer.observe(s))

  // ── Smooth anchor scroll ──
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'))
      if (target) {
        e.preventDefault()
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    })
  })

  // ── Fade-in on scroll ──
  const fadeEls = document.querySelectorAll('.cmd-card, .stack-item, .arch-source-chip, .problem-node')
  const fadeObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1'
        entry.target.style.transform = 'translateY(0)'
        fadeObs.unobserve(entry.target)
      }
    })
  }, { threshold: 0.1 })

  fadeEls.forEach(el => {
    el.style.opacity = '0'
    el.style.transform = 'translateY(16px)'
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease'
    fadeObs.observe(el)
  })

})
