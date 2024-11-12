let savedTexts = [];

// 드래그된 텍스트 저장
chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
  console.log("백그라운드 메시지 수신");
  if (request.type === "open_side_panel") {
    await chrome.sidePanel.open({tabId: sender.tab.id});
    await chrome.sidePanel.setOptions({
      tabId: sender.tab.id,
      path: "sidebar.html",
      enabled: true, // 반드시 true로 설정해야 활성화됨
    });
    savedTexts.push(request.text);
    chrome.storage.local.set({ savedTexts });  // 저장
  }
});

// 사이드바 요청을 위한 메시지 처리
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "get_saved_texts") {
    chrome.storage.local.get("savedTexts", (data) => {
      sendResponse(data.savedTexts || []);
    });
    return true; // 비동기 응답을 위한 리턴값
  }
});