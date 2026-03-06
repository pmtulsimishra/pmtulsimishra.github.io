// ===========================
// NAVBAR SCROLL EFFECT
// ===========================
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
});

// ===========================
// MOBILE NAV TOGGLE
// ===========================
const toggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');
toggle.addEventListener('click', () => navLinks.classList.toggle('open'));
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => navLinks.classList.remove('open'));
});

// ===========================
// ACTIVE NAV HIGHLIGHT ON SCROLL
// ===========================
const sections = document.querySelectorAll('section[id], header[id]');
const navAnchors = document.querySelectorAll('.nav-links a:not(.nav-resume-btn)');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(sec => {
    if (window.scrollY >= sec.offsetTop - 100) current = sec.id;
  });
  navAnchors.forEach(a => {
    a.style.color = a.getAttribute('href') === `#${current}` ? 'var(--primary)' : '';
  });
});

// ===========================
// SCROLL-TRIGGERED FADE-IN
// ===========================
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll(
  '.tl-content, .edu-card, .cert-card, .award-card, .vol-item, .stat, ' +
  '.skill-tag, .contact-card, .lang-item, .membership-box, ' +
  '.interest-card, .pillar, .faq-item, .stoic-card'
).forEach(el => {
  el.classList.add('fade-in');
  observer.observe(el);
});

// ===========================
// STOIC QUOTE OF THE DAY
// ===========================
const stoicQuotes = [
  { quote: "You have power over your mind — not outside events. Realize this, and you will find strength.", author: "Marcus Aurelius" },
  { quote: "The impediment to action advances action. What stands in the way becomes the way.", author: "Marcus Aurelius" },
  { quote: "Waste no more time arguing what a good man should be. Be one.", author: "Marcus Aurelius" },
  { quote: "Very little is needed to make a happy life; it is all within yourself, in your way of thinking.", author: "Marcus Aurelius" },
  { quote: "If it is not right, do not do it; if it is not true, do not say it.", author: "Marcus Aurelius" },
  { quote: "Begin at once to live, and count each separate day as a separate life.", author: "Seneca" },
  { quote: "It is not that I am brave, but that I choose what to fear.", author: "Seneca" },
  { quote: "We suffer more in imagination than in reality.", author: "Seneca" },
  { quote: "Luck is what happens when preparation meets opportunity.", author: "Seneca" },
  { quote: "No man was ever wise by chance.", author: "Seneca" },
  { quote: "Hang on to your youthful enthusiasms — you'll be able to use them better when you're older.", author: "Seneca" },
  { quote: "Do not indulge in hopes that outrun possibility.", author: "Seneca" },
  { quote: "Make the best use of what is in your power, and take the rest as it happens.", author: "Epictetus" },
  { quote: "He is a wise man who does not grieve for the things which he has not, but rejoices for those which he has.", author: "Epictetus" },
  { quote: "First say to yourself what you would be; and then do what you have to do.", author: "Epictetus" },
  { quote: "Seek not the good in external things; seek it in yourself.", author: "Epictetus" },
  { quote: "It's not what happens to you, but how you react to it that matters.", author: "Epictetus" },
  { quote: "Men are disturbed not by the things which happen, but by the opinions about the things.", author: "Epictetus" },
  { quote: "Don't explain your philosophy. Embody it.", author: "Epictetus" },
  { quote: "Wealth consists not in having great possessions, but in having few wants.", author: "Epictetus" },
  { quote: "The happiness of your life depends upon the quality of your thoughts.", author: "Marcus Aurelius" },
  { quote: "Accept the things to which fate binds you, and love the people with whom fate brings you together.", author: "Marcus Aurelius" },
  { quote: "The object of life is not to be on the side of the majority, but to escape finding oneself in the ranks of the insane.", author: "Marcus Aurelius" },
  { quote: "Never let the future disturb you. You will meet it, if you have to, with the same weapons of reason which today arm you against the present.", author: "Marcus Aurelius" },
  { quote: "Confine yourself to the present.", author: "Marcus Aurelius" },
  { quote: "How long will you wait before you demand the best for yourself?", author: "Epictetus" },
  { quote: "True happiness is to enjoy the present without anxious dependence upon the future.", author: "Seneca" },
  { quote: "Difficulties strengthen the mind, as labor does the body.", author: "Seneca" },
  { quote: "Sometimes even to live is an act of courage.", author: "Seneca" },
  { quote: "A gem cannot be polished without friction, nor a person perfected without trials.", author: "Seneca" },
  { quote: "Retire into yourself as much as possible.", author: "Marcus Aurelius" },
  { quote: "Loss is nothing else but change, and change is Nature's delight.", author: "Marcus Aurelius" },
  { quote: "The first rule is to keep an untroubled spirit. The second is to look things in the face and know them for what they are.", author: "Marcus Aurelius" },
  { quote: "Be tolerant with others and strict with yourself.", author: "Marcus Aurelius" },
  { quote: "The best answer to anger is silence.", author: "Marcus Aurelius" },
  { quote: "Dwell on the beauty of life. Watch the stars, and see yourself running with them.", author: "Marcus Aurelius" },
  { quote: "It does not matter how slowly you go as long as you do not stop.", author: "Epictetus" },
  { quote: "We are more often frightened than hurt; and we suffer more from imagination than from reality.", author: "Seneca" },
  { quote: "Begin at once to live and count each day as a separate life.", author: "Seneca" },
  { quote: "Time is the only true currency. Invest it wisely.", author: "Seneca" },
];

function getStoicQuoteOfTheDay() {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff = now - start;
  const dayOfYear = Math.floor(diff / (1000 * 60 * 60 * 24));
  return stoicQuotes[dayOfYear % stoicQuotes.length];
}

const todayQuote = getStoicQuoteOfTheDay();
document.getElementById('stoic-quote').textContent = todayQuote.quote;
document.getElementById('stoic-author').textContent = `— ${todayQuote.author}`;

const today = new Date();
document.getElementById('stoic-date').textContent =
  today.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

// ===========================
// FAQ ACCORDION
// ===========================
document.querySelectorAll('.faq-q').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.parentElement;
    const isOpen = item.classList.contains('open');
    // Close all
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    // Toggle clicked
    if (!isOpen) item.classList.add('open');
  });
});

// ===========================
// AMA FORM — mailto fallback
// ===========================
document.getElementById('ama-form').addEventListener('submit', function (e) {
  e.preventDefault();
  const name = document.getElementById('ama-name').value.trim();
  const question = document.getElementById('ama-question').value.trim();
  const feedback = document.getElementById('ama-feedback');

  if (!name || !question) return;

  const subject = encodeURIComponent(`Question from ${name} via tulsimishra.com`);
  const body = encodeURIComponent(`Hi Tulsi,\n\n${name} asked:\n\n"${question}"\n\n— Sent via your website`);
  window.location.href = `mailto:mishratulsi1991@gmail.com?subject=${subject}&body=${body}`;

  feedback.textContent = 'Opening your email client... Thanks for reaching out!';
  this.reset();
  setTimeout(() => { feedback.textContent = ''; }, 5000);
});
