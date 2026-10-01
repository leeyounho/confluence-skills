# 복사·붙여넣기용 출력

## HTML 파일

UTF-8 독립 HTML 문서를 만든다. 외부 라이브러리, JavaScript, 외부 폰트 없이 열 수 있어야 한다. 복사할 본문은 `<main id="confluence-body">`에 넣는다. 안내 문구는 HTML 본문 밖의 최종 응답에 둔다.

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>문서 제목</title>
  <style>
    body { max-width: 960px; margin: 40px auto; padding: 0 24px;
           font-family: sans-serif; line-height: 1.65; color: #172b4d; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #b3bac5; padding: 8px; text-align: left;
             vertical-align: top; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; padding: 12px;
          background: #f4f5f7; }
    code { font-family: monospace; }
  </style>
</head>
<body>
  <h1>문서 제목</h1>
  <main id="confluence-body">
    <p>문서의 목적과 핵심 내용을 요약한다.</p>
    <h2>본문의 첫 번째 주제</h2>
    <p>실제 문서 내용.</p>
  </main>
</body>
</html>
```

위 예시는 파일 구조만 보여준다. 실제 산출물에서는 예시 문구를 실제 내용으로 대체한다. CSS는 로컬 가독성을 위한 것이며 Confluence가 보존한다고 가정하지 않는다.

## 표현 선택

| 요소 | 권장 표현 | 주의점 |
| --- | --- | --- |
| 제목 | 본문은 h2, 하위 주제는 h3부터 | 굵은 문단으로 제목 계층을 대신하지 않는다. |
| 문단 | p, strong, em | 색상만으로 의미를 전달하지 않는다. |
| 목록 | ul/ol/li | 단계는 번호 목록, 병렬 항목은 글머리표. |
| 표 | table/thead/tbody/tr/th/td | 셀 병합·중첩 표를 피한다. 긴 절차·코드는 표 밖에 둔다. |
| 링크 | a href | 사용자 제공 링크나 실제 확인한 링크만 사용한다. |
| 코드 | pre/code, 짧은 토큰은 code | 코드의 줄바꿈과 들여쓰기를 보존한다. 언어는 바로 앞에 표시한다. |
| 주의/팁 | 제목 또는 굵은 레이블 + 문단 | Confluence 패널 매크로로 자동 변환된다고 주장하지 않는다. |
| 체크 항목 | 일반 목록의 완료/미완료 텍스트 | 네이티브 작업 항목이나 담당자 멘션으로 변환된다고 가정하지 않는다. |
| 다이어그램 | 설명 + 필요하면 이미지 파일 | Mermaid 원문을 붙여넣으면 다이어그램이 생긴다고 가정하지 않는다. |

- 텍스트 노드의 `&`, `<`, `>`와 속성 값의 따옴표를 적절히 이스케이프한다. 코드에도 동일하게 적용한다. 원본 코드를 실행 가능한 HTML로 삽입하지 않는다.
- 사용자 자료의 링크를 유지하되 `javascript:` 같은 실행 URL을 산출물에 넣지 않는다.
- `{toc}`, `{code}`, `h1.` 등 wiki markup, `ac:` 매크로, HTML 폼, iframe은 기본 붙여넣기 문서에 넣지 않는다.
- 이미지 없이 이해할 수 있는 설명을 제공한다. 이미지가 필요하면 실제 파일을 제공하거나 `이미지 삽입 위치: ...`로 표시한다. 존재하지 않는 파일을 링크하지 않는다.
- 목차가 필요한 긴 문서는 간단한 텍스트 목차를 쓰거나 Confluence에서 목차 요소를 추가하도록 안내한다. 브라우저 파일의 앵커가 Confluence에서도 그대로 작동한다고 보장하지 않는다.

## 확인

HTML과 Markdown의 내용·표 셀·코드가 일치하는지 확인한다. 문서 제목이 본문에 반복되지 않는지, 제목 계층이 일관되는지 확인한다. 파일의 UTF-8 인코딩과 HTML 기본 구조를 확인한다.

실제 편집기에서 검증할 수 있으면 일반 붙여넣기 후 표의 열, 코드 줄바꿈, 링크 대상을 확인한다. 네이티브 코드 블록으로 자동 변환되지 않으면 Confluence에서 코드 블록을 추가하고 해당 코드만 복사하도록 안내한다. 붙여넣기 검증을 위해 사용자의 요청 없이 페이지를 게시하지 않는다.

## 공식 근거

2026-10-01 확인. 편집기 기능에 의존하는 작업에서는 최신 공식 안내를 확인한다.

- [Confluence Cloud: Import external documents](https://support.atlassian.com/confluence-cloud/docs/import-content-into-confluence-cloud/): 기본 서식이 있는 텍스트를 편집기에 붙여넣을 수 있다. Word 가져오기는 별도 기능이다. 이 안내가 HTML/CSS 전체의 보존을 보장하는 것은 아니다.
