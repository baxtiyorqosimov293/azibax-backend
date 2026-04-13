const readerBookTitle = document.getElementById("readerBookTitle");
const readerBookAuthor = document.getElementById("readerBookAuthor");
const readerText = document.getElementById("readerText");
const readerStatus = document.getElementById("readerStatus");
const fontMinusBtn = document.getElementById("fontMinusBtn");
const fontPlusBtn = document.getElementById("fontPlusBtn");

let currentFontSize = Number(localStorage.getItem("azibax_reader_font") || 20);

function getParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    id: params.get("id") || "",
    title: params.get("title") || "Без названия",
    author: params.get("author") || "Неизвестный автор",
  };
}

function applyFontSize() {
  if (readerText) {
    readerText.style.fontSize = `${currentFontSize}px`;
  }
  localStorage.setItem("azibax_reader_font", String(currentFontSize));
}

fontMinusBtn?.addEventListener("click", () => {
  currentFontSize = Math.max(16, currentFontSize - 1);
  applyFontSize();
});

fontPlusBtn?.addEventListener("click", () => {
  currentFontSize = Math.min(30, currentFontSize + 1);
  applyFontSize();
});

async function loadReaderBook() {
  const { id, title, author } = getParams();

  if (!id) {
    readerBookTitle.textContent = "Книга не найдена";
    readerBookAuthor.textContent = "AziBax Reader";
    readerText.textContent = "Не передан идентификатор книги.";
    readerStatus.textContent = "Ошибка";
    return;
  }

  try {
    readerStatus.textContent = "Загружаем книгу...";
    readerBookTitle.textContent = title;
    readerBookAuthor.textContent = author;

    const readData = await apiFetch(`/books/read?book_id=${encodeURIComponent(id)}`);

    readerText.textContent = readData.text || "Текст книги пока не добавлен.";
    readerStatus.textContent = "Книга открыта";
  } catch (err) {
    console.error(err);
    readerBookTitle.textContent = title || "Ошибка загрузки";
    readerBookAuthor.textContent = author || "AziBax Reader";
    readerText.textContent = err.message || "Не удалось открыть книгу.";
    readerStatus.textContent = "Ошибка";
  }
}

applyFontSize();
loadReaderBook();
