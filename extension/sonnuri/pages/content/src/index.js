//
import createTranslateButton from './components/sentence/createTranslateButton.js';
import createTranslateImgWrapper from './components/sentence/createTraslateImgWrapper.js';
import loadingCircle from './components/sentence/loadingCircle.js';

import createModal from './components/word/createModal.js';
import createOverlay from './components/word/createOverlay.js';
import createToggleButton from './components/word/createToggleButton.js';
import handleMouseMoveOnCanvas from './components/word/handleMouseMoveOnCanvas.js';
import hideVideoModal from './components/word/hideVideoModal.js';
import highlightTextNodes from './components/word/highlightTextNodes.js';
import showVideoModal from './components/word/showVideoModal.js';
import serverWords from './words.js';

CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius) {
  this.beginPath();
  this.moveTo(x + radius, y);
  this.lineTo(x + width - radius, y);
  this.quadraticCurveTo(x + width, y, x + width, y + radius);
  this.lineTo(x + width, y + height - radius);
  this.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  this.lineTo(x + radius, y + height);
  this.quadraticCurveTo(x, y + height, x, y + height - radius);
  this.lineTo(x, y + radius);
  this.quadraticCurveTo(x, y, x + radius, y);
  this.closePath();
};

let highlights = [];

const modal = createModal();
const { overlay, canvas, ctx } = createOverlay();

// 캔버스 오버레이 생성

// 캔버스 크기 설정
function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

// 초기 설정 및 이벤트 리스너
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

const { highlights: newHighlights, isHighlighting } = createToggleButton(
  ctx,
  canvas,
  highlights,
  serverWords,
  isElementCovered,
);
// 요소가 가려져 있는지 확인하는 함수
function isElementCovered(rect) {
  const elements = document.elementsFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
  return elements.some(element => {
    return getComputedStyle(element).zIndex !== 'auto' && element !== canvas;
  });
}
// 마우스 이동 이벤트 처리
document.addEventListener('mousemove', e => handleMouseMoveOnCanvas(e, highlights, modal, showVideoModal));

// 버튼 생성햐
const translateSentenceBtn = createTranslateButton();
// 버튼에 설명하는 수어 이미지 추가
const translateImgWrapper = createTranslateImgWrapper();

translateSentenceBtn.addEventListener('mouseenter', e => {
  if (translateImgWrapper.style.display === 'none') {
    console.log('mouseenter');
    translateImgWrapper.style.left = `${e.pageX + 5}px`;
    translateImgWrapper.style.top = `${e.pageY + 5}px`;
    translateImgWrapper.style.display = 'block';
  }
});

translateSentenceBtn.addEventListener('mouseleave', () => {
  translateImgWrapper.style.display = 'none';
});

// 로딩 컨테이너 생성
const loadingContainer = document.createElement('div');
loadingContainer.id = 'loading-container';
document.body.appendChild(loadingContainer);

// 문장 수어번역 요청 로딩 아이콘
const { loadingCircleWrapper, circle: loadingCircleElement } = loadingCircle();
loadingContainer.appendChild(loadingCircleWrapper);

// 보간 비디오 생성 요청 로딩 아이콘
const {loadingCircleWrapper: loadingMakeVideoCircleWrapper, circle: loadingMakeVideoCircleElement } = loadingCircle();
loadingContainer.appendChild(loadingMakeVideoCircleWrapper);

// 하이라이트 생성
if (isHighlighting) {
  setTimeout(() => {
    highlights = highlightTextNodes(ctx, canvas, document.body, highlights, serverWords, isElementCovered);
  }, 300);
}
document.addEventListener('mouseup', e => {
  const selectedText = window.getSelection().toString(); // 드래그된 단어 가져오기
  if (selectedText) {
    translateSentenceBtn.style.top = `${e.pageY}px`; // 버튼 위치 변경
    translateSentenceBtn.style.left = `${e.pageX}px`; // 버튼 위치 변경
    translateSentenceBtn.style.display = 'flex'; // 플렉스 박스 사용
    translateSentenceBtn.style.alignItems = 'center'; // 수직 중앙 정렬
    translateSentenceBtn.style.justifyContent = 'center'; // 수평 중앙 정렬

    // 버튼 클릭 이벤트
    // 백그라운드에 request_sentence 요청을 보내 백엔드 서버에 문장을 요청하고, 로딩상태를 변경한다.
    translateSentenceBtn.onclick = async () => {
      // 로딩 아이콘을 표시한다.
      await chrome.runtime.sendMessage({
        type: 'open_side_panel',
      });
      // 백그라운드에 request_sentence 요청을 보내 백엔드 서버에 문장을 요청하고, 로딩상태를 변경한다.
      await chrome.runtime.sendMessage({
        type: 'request_sentence',
        text: selectedText,
      });
      translateSentenceBtn.style.display = 'none'; // 버튼 제거
    };
  } else {
    translateSentenceBtn.style.display = 'none'; // 선택된 텍스트가 없으면 버튼 숨김
  }
  return true;
});

// 백그라운드에서 요청이 완료되었을 때, 아이콘의 상태를 변경한다.
// 또한 비디오 주소 리스트를 받아와서, 보간된 비디오 생성 요청을 보낸다.
chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'success_sentence_result') {
    console.log('요청결과 전송받기 완료');
    loadingCircleElement.success();
    console.log('컨텐츠 스크립트 message.urls', message.urls);
    chrome.runtime.sendMessage({
      type: 'request_make_video',
      urls: message.urls,
    });
  }
});

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'success_make_video_result') {
    loadingMakeVideoCircleElement.success();
    console.log('보간 비디오 생성 요청 결과 전송받기 완료');
  }
});



chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'error_sentence_result') {
    loadingCircleElement.error();
  }
});

// 이벤트 리스너 수정
canvas.addEventListener('mouseleave', () => hideVideoModal(modal));

// canvas.addEventListener('DOMContentLoaded', () => {

window.addEventListener('popstate', () => {
  if (isHighlighting) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setTimeout(() => {
      highlights = highlightTextNodes(ctx, canvas, document.body, highlights, serverWords, isElementCovered);
    }, 300);
  }
});

window.addEventListener('resize', () => {
  if (isHighlighting) {
    highlights = highlightTextNodes(ctx, canvas, document.body, highlights, serverWords, isElementCovered);
  }
});

// react, next 화면이동감지
document.addEventListener('click', event => {
  if (isHighlighting) {
    // 하이라이트 초기화
    // ctx.clearRect(0, 0, canvas.width, canvas.height);
    setTimeout(() => {
      highlights = highlightTextNodes(ctx, canvas, document.body, highlights, serverWords, isElementCovered);
    }, 300);
  }
});

// 페이지 언로드 시 정리
window.addEventListener(
  'beforeunload',
  () => {
    cleanup();
  },
  { capture: true },
);

// 컨트롤 패널 생성 - 하이라이트 토글 버튼

highlights = newHighlights;

// 스크롤 이벤트 처리
let scrollTimeout;
window.addEventListener('scroll', () => {
  if (isHighlighting) {
    // 스크롤 중에는 캔버스 숨기기
    canvas.style.display = 'none';
    // 스크롤이 멈추면 다시 그리기
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      canvas.style.display = 'block';
      highlights = highlightTextNodes(ctx, canvas, document.body, highlights, serverWords, isElementCovered);
    }, 100);
  }
});

// 윈도우 리사이즈 시 다시 그리기


// cleanup 함수
function cleanup() {
  // 비디오 정리
  const videos = document.querySelectorAll('video');
  videos.forEach(video => {
    video.pause();
    video.removeAttribute('src');
    video.load();
  });

  // 이벤트 리스너 제거
  window.removeEventListener('resize', resizeCanvas);
  document.removeEventListener('mousemove', handleMouseMoveOnCanvas);

  // DOM 요소 정리
  if (modal) modal.remove();
  if (canvas) canvas.remove();
  if (overlay) overlay.remove();

  // 하이라이트 정리
  if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
  highlights = [];
}