// insertUser.js
const pool = require('./db');

async function insertUser(name, email) {
  try {
    const query = 'INSERT INTO users (name, email) VALUES (?, ?)';
    const [result] = await pool.execute(query, [name, email]);
    console.log('삽입 성공! ID:', result.insertId);
  } catch (err) {
    console.error('삽입 실패:', err);
  }
}

// 예시 실행
insertUser('홍길동', 'hong@example.com');