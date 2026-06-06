/**
 * 복용 완료 버튼용 Google Apps Script
 *
 * 1. script.google.com → 새 프로젝트 → 이 코드 붙여넣기
 * 2. 프로젝트 설정 → 스크립트 속성:
 *    - MARK_SECRET  : GitHub Secret MEDICATION_MARK_SECRET 와 동일한 임의 문자열
 *    - GITHUB_PAT   : job-alert Actions 권한 PAT (github_pat_...)
 *    - GITHUB_REPO  : gkrdlsdhk-cpa/job-alert
 * 3. 배포 → 새 배포 → 웹 앱 → execute as: Me, access: Anyone
 * 4. 배포 URL + ?key=MARK_SECRET 값을 config.yaml mark_taken_url 에 넣기
 */
function doGet(e) {
  var props = PropertiesService.getScriptProperties();
  var expected = props.getProperty('MARK_SECRET');
  var key = (e && e.parameter && e.parameter.key) || '';
  if (!expected || key !== expected) {
    return HtmlService.createHtmlOutput('<h2>인증 실패</h2>');
  }

  var repo = props.getProperty('GITHUB_REPO') || 'gkrdlsdhk-cpa/job-alert';
  var pat = props.getProperty('GITHUB_PAT');
  if (!pat) {
    return HtmlService.createHtmlOutput('<h2>GITHUB_PAT 미설정</h2>');
  }

  var url =
    'https://api.github.com/repos/' +
    repo +
    '/actions/workflows/medication-mark-taken.yml/dispatches';
  var options = {
    method: 'post',
    headers: {
      Authorization: 'Bearer ' + pat,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    payload: JSON.stringify({
      ref: 'main',
      inputs: { mark_secret: key },
    }),
    muteHttpExceptions: true,
  };

  var res = UrlFetchApp.fetch(url, options);
  var code = res.getResponseCode();
  if (code === 204) {
    return HtmlService.createHtmlOutput(
      '<html><body style="font-family:sans-serif;text-align:center;padding:2rem;">' +
        '<h1>✅ 복용 완료</h1><p>오늘 복약 체크했어요.</p></body></html>'
    ).setTitle('복약 완료');
  }

  return HtmlService.createHtmlOutput(
    '<h2>기록 실패 (HTTP ' + code + ')</h2><pre>' + res.getContentText() + '</pre>'
  );
}
