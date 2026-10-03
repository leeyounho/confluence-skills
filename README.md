# Confluence Skills

Claude와 Codex에서 Confluence 문서를 작성하는 스킬과 자체 플러그인 marketplace입니다.

기술 설계서, 운영 절차서, 회의록, 장애 보고서를 **HTML 소스 입력용 본문 조각 + 수정용 Markdown**으로 만듭니다. 필요한 다이어그램은 PNG와 개별 도형을 편집할 수 있는 `.drawio` 원본으로 제공합니다. 문서 작성 자체는 Confluence 연결이 필요 없는 지침형 스킬입니다. PNG 렌더링에는 사용 환경의 로컬 렌더링 도구가 필요하며, 없는 경우 원본과 내보내기 안내를 제공합니다.

## Claude Code 설치

Claude Code 세션에서 실행합니다.

```text
/plugin marketplace add leeyounho/confluence-skills
/plugin install confluence-docs@confluence-skills
```

설치 후 스킬을 호출합니다.

```text
/confluence-docs:confluence-doc-writer 이 메모를 Confluence용 운영 절차서로 작성해줘.
```

## Codex 설치

지원하는 Codex CLI에서 marketplace를 추가합니다.

```text
codex plugin marketplace add leeyounho/confluence-skills
```

데스크톱 앱의 Plugins 목록에서 **Confluence Skills**를 선택하고 **confluence-docs**를 설치합니다. 새 채팅에서 스킬을 선택하거나 다음과 같이 요청합니다.

```text
Confluence 문서 작성 스킬을 사용해 이 메모로 붙여넣기용 HTML과 Markdown을 만들어줘.
```

플러그인 UI나 marketplace 명령을 지원하지 않는 환경은 아래 수동 설치를 사용합니다.

## Claude 웹/앱 및 수동 설치

[최신 Release](https://github.com/leeyounho/confluence-skills/releases/latest)에서 `confluence-doc-writer.zip`을 받습니다.

- **Claude 웹/앱:** Skills 설정에서 ZIP을 업로드하고 활성화합니다.
- **Claude Code 개인 스킬:** ZIP 안의 `confluence-doc-writer` 폴더를 `~/.claude/skills/`에 복사합니다. 호출은 `/confluence-doc-writer`입니다.
- **Codex 개인 스킬:** 같은 폴더를 `~/.agents/skills/`에 복사합니다. 호출은 `$confluence-doc-writer`입니다. 사용 중인 버전이 기존 `~/.codex/skills/`를 사용하면 그 경로를 따릅니다.

수동 ZIP 설치본은 GitHub 수정만으로 자동 갱신되지 않습니다. 플러그인 설치본과 동일한 스킬을 중복 설치하지 마세요.

## 원하는 템플릿 추가

템플릿과 스킬을 따로 보관하면 집에서 스킬을 개발하고 회사에서는 회사 양식을 추가해 쓸 수 있습니다. 스킬 업데이트로 사용자 양식을 덮어쓰지 않습니다.

회사 작업 폴더에 다음처럼 둡니다. `.md`는 UTF-8 Markdown이며 HTML 양식도 사용할 수 있습니다.

```text
회사-작업폴더/
├── confluence-docs.config.json
└── .confluence-docs/
    └── templates/
        ├── operations.md
        └── meeting.md
```

`confluence-docs.config.example.json`을 작업 폴더에 `confluence-docs.config.json`으로 복사하고 기본 양식을 지정합니다. `template_root`는 설정 파일 기준 상대 경로 또는 절대 경로입니다.

```json
{
  "template_root": "./.confluence-docs/templates",
  "default_template": "operations.md"
}
```

`operations.md`를 실제로 해당 폴더에 넣어야 합니다. 시작할 때는 `plugins/confluence-docs/skills/confluence-doc-writer/assets/templates/`의 예시를 복사해서 수정할 수 있습니다. 제목과 목차, 표를 만들고 채울 곳에 `{{목적}}`, `{{담당자}}`처럼 자리표시자를 씁니다. 자리표시자 없이 작성된 기존 문서도 양식으로 지정할 수 있습니다.

```text
Confluence 문서 작성 스킬을 사용해 operations 템플릿으로 이 메모를 정리해줘.
```

설정 없이 파일 경로를 바로 지정할 수도 있습니다.

```text
Confluence 문서 작성 스킬을 사용해 D:/CompanyTemplates/운영절차서.md 양식으로 작성해줘.
```

요청에서 지정한 양식이 기본 설정보다 우선합니다. 양식의 목차·표·고정 문구를 유지하며 부족하거나 애매한 정보는 먼저 질문합니다. 미정·확인 예정·해당 없음으로 작성하는 것은 사용자가 그 상태와 표현을 확인한 경우에만 허용합니다. 지정 파일을 찾을 수 없으면 임의의 양식으로 대체하지 않습니다.

**완료보고:** 공개 `completion-report.md` 템플릿은 **summary → 배경 → 효과 → 추진내용 → 향후계획** 순서로 작성합니다. 효과는 확인된 실적과 기대 효과를 구분하고, 추진내용에는 실제 수행 작업과 완료 상태를 담습니다.

```text
Confluence 문서 작성 스킬을 사용해 완료보고로 작성해줘.
첨부 메모를 바탕으로 본문 HTML 소스와 수정용 Markdown을 만들어줘.
```

## 템플릿 목록과 작성 준비 상태

한국어 이름으로 **완료보고, 운영 절차서, 회의록, 현황 보고**를 선택할 수 있습니다. `완료 보고`와 `완료보고서`도 완료보고 양식으로 선택합니다. `사용 가능한 템플릿 보여줘`라고 하면 공개 양식과 접근 가능한 로컬 양식을 안내하며 문서 생성은 시작하지 않습니다. 명시한 양식은 설정의 기본 양식보다 우선합니다.

회사 양식에 이름을 붙이려면 로컬 `confluence-docs.config.json`에 `"template_aliases": {"완료보고": "사내완료.md"}`를 추가하고 해당 파일을 template_root 안에 둡니다. 로컬 별칭과 동일 파일명이 공개 양식보다 우선하며, 지정한 회사 파일이 없으면 공개 양식으로 대체하지 않습니다. 회사 양식의 필수·선택 기준은 해당 파일의 작성 안내에 지정합니다.

정보 수집 중에는 항목별로 **확인 완료 / 질문 필요 / 미정 표현 합의 / 없음 표현 합의 / 자동 요약 / 선택 항목 생략** 상태를 관리합니다. `작성 준비 상태 보여줘`로 남은 항목을 확인할 수 있습니다. 완료보고의 summary는 확인된 본문에서 요약하며 별도로 묻지 않습니다. 수치가 있는 효과에는 비교 기준·기간·단위를 확인합니다. 선택 항목 때문에 질문을 불필요하게 늘리지 않습니다.

공개 양식의 기준은 스킬의 `assets/templates/catalog.json`에 있습니다. 같은 파일명으로 만든 회사 양식에도 공개 기준을 강제로 적용하지 않습니다.

## 특정 부분 수정

```text
이 완료보고에서 효과만 수정해줘. 실측 개선율은 20%에서 15%로 정정됐어.
```

기존 문서를 읽고 지정한 부분과 관련 summary만 수정합니다. 다른 본문 섹션은 유지하고 이미 확인한 내용을 다시 묻지 않습니다. 수정이 다른 본문에도 영향을 주면 추가 범위를 확인합니다. HTML·Markdown과 기존 미리보기를 함께 갱신하고 영향을 받지 않은 그림은 다시 생성하지 않습니다.

## 회사에서 로컬 검사

Python이 있으면 별도 패키지·네트워크·GitHub Actions 없이 아래 도구를 실행할 수 있습니다. `<스킬폴더>`를 설치한 confluence-doc-writer 경로로 바꿉니다. 공백이 있는 경로는 따옴표로 감쌉니다.

```text
python <스킬폴더>/scripts/templates.py --list
python <스킬폴더>/scripts/templates.py --select 완료보고
python <스킬폴더>/scripts/validate_body.py <문서.body.html>
```

HTML 검사는 문서 외곽 태그, 남은 자리표시자·작성 주석, 태그 닫힘, 로컬 이미지 경로 등을 확인하고 오류가 있으면 실패 상태를 반환합니다. 파일을 고치거나 덮어쓰지 않습니다. 코드 예제의 중괄호와 코드 펜스는 허용합니다.

준비 상태는 기본적으로 대화에서 관리합니다. 별도 상태 파일을 요청한 경우 `templates.py --select 완료보고 --state <상태파일.json>`으로 공개 양식의 누락·충돌 상태를 검사할 수 있습니다. 이 도구는 기록된 상태를 검사하며 사용자 답변의 사실성을 자동 판단하지 않습니다. Python 실행이 불가능한 Claude 웹 등에서는 같은 기준으로 수동 검토하고 검사 실행 여부를 정확히 안내합니다.

**집에서는 공개 스킬과 일반 예시를 관리하고, 회사 양식은 회사의 로컬 폴더나 승인된 내부 저장소에서 관리합니다.** 이 저장소는 `.confluence-docs/`와 실제 `confluence-docs.config.json`을 Git에서 제외합니다. 다른 프로젝트에서도 해당 제외 규칙을 적용해야 합니다. 경로나 설정 파일만으로 회사 파일이 다른 컴퓨터에 동기화되지는 않습니다.

Claude 웹/앱에서는 해당 세션에 양식 파일을 첨부해 지정합니다. 로컬 폴더 설정이 웹 환경에 자동 적용되지는 않습니다.

## 보고자료 다이어그램

공개 `report.md` 예시를 복사하거나 회사 템플릿의 그림 위치에 다음 주석을 추가합니다.

```markdown
<!-- 시각화
id: process-flow
종류: 흐름도
필수 여부: 선택
목적: 정상 처리와 실패 시 분기를 설명한다.
생성 조건: 분기·반복·예외가 있어 글이나 목록만으로 이해하기 어려울 때
생략 조건: 단순한 순서이거나 본문·표의 정보를 반복할 때
출력: PNG + draw.io 원본
자료 부족 시: 생성하지 않는다
-->
```

그림 위치는 생성 후보입니다. 필요한 경우에만 만들고, 생략하면 빈 공간이나 '그림 없음' 표시를 남기지 않습니다. 필수로 지정해도 자료가 부족하면 추측하지 않습니다. 시각화 주석은 완성 문서에서 제거합니다.

기본 산출물은 `diagrams/process-flow.drawio`와 `diagrams/process-flow.png`입니다. 브라우저용 `.preview.html`에 PNG를 배치하고 원본은 별도로 제공합니다. 입력용 `.body.html`에는 확인된 Confluence 첨부 URL이 있을 때만 이미지를 넣고, 없으면 그림 삽입 위치와 파일을 전달합니다. Mermaid를 명시하면 `.mmd` 원본도 사용할 수 있지만 draw.io 원본과 같은 형식은 아닙니다.

**Confluence에서 편집:** 본문 HTML 소스를 입력하고 적용한 다음 그림 위치에 draw.io Diagram 요소를 추가하고 `.drawio` 원본을 가져옵니다. 설치된 draw.io 앱에서 도형·문구·연결선을 수정합니다. 앱이 없으면 PNG를 첨부하고 원본을 별도로 편집해 다시 내보냅니다. HTML을 붙여넣는 것만으로 draw.io 요소가 생성되지는 않습니다.

문서와 `diagrams/` 폴더를 함께 보관하면 로컬 미리보기 HTML에서 상대 경로 이미지가 표시됩니다. 이 상대 경로로 회사 Confluence에서 이미지가 표시된다고 가정하지 않습니다. PNG 생성 도구가 없는 환경에서는 원본만 제공하고 미생성 상태를 명시합니다. 회사 자료를 원격 렌더링 서비스에 자동 전송하지 않습니다.

매크로는 패널·접기·목차 등 삽입 위치와 안내를 제공하며, 기본 붙여넣기 방식에서 자동 생성된다고 보장하지 않습니다.

```text
Confluence 문서 작성 스킬을 사용해 report 템플릿으로 작성해줘.
다이어그램은 이해에 도움이 될 때만 넣고 PNG와 편집용 draw.io 원본을 제공해줘.
```

## 문서 사용

1. 메모나 파일을 제공하고 문서 작성을 요청합니다. 처음에는 간단하거나 거친 설명으로 시작해도 됩니다.
2. 스킬이 확인된 내용과 부족한 정보를 정리하고 필요한 질문을 한 번에 1~3개씩 합니다. 답변을 통해 템플릿 항목을 채우며 애매한 사실을 임의로 확정하지 않습니다.
3. 정보가 충분해지면 별도 승인 질문 없이 최종 파일을 만듭니다. 처음부터 자료가 충분하면 바로 작성합니다. 중간 초안은 요청 시 제공하며 미확정 사항을 표시합니다.
4. 생성된 **`<slug>.body.html`을 텍스트/코드 편집기로 열고 소스 전체를 복사**합니다.
5. 제목은 Confluence 제목 필드에 입력합니다.
6. **HTML 소스 입력 창**에 복사한 내용을 붙여넣고 적용합니다.
7. 표, 코드 줄바꿈, 링크를 확인합니다. 필요한 이미지는 별도로 첨부합니다.

`.body.html`에는 `<body>` 안쪽의 내용만 들어갑니다. `<body>` 태그 자체와 `DOCTYPE`, `<html>`, `<head>`, `<style>`, 페이지 제목, 코드 펜스는 포함하지 않습니다. 더 이상 본문만 따로 골라 복사할 필요가 없습니다.

선택 산출물 `.preview.html`은 브라우저 확인용 전체 HTML이고 `.md`는 수정용입니다. 입력 창에 넣는 파일은 `.body.html`입니다. 예를 들어 본문 파일의 전체 내용은 다음과 같습니다.

```html
<p>이번 보고의 핵심 요약입니다.</p>
<h2>진행 현황</h2>
<ul>
  <li>확인된 진행 내용을 작성합니다.</li>
</ul>
```

HTML 소스 입력 기능의 지원 범위는 회사의 설치 앱·편집기에 따라 다릅니다. 이 기본 출력은 사용자의 회사에서 동작한 본문 조각 방식에 맞춥니다. 일반 편집기에 서식 복사를 원하면 요청에서 지정하고 미리보기의 보이는 본문을 복사합니다. 페이지를 자동 게시하지 않습니다.

## 업데이트

**Claude Code:** `/plugin` → Marketplaces → Confluence Skills에서 **Enable auto-update**를 켜거나 아래 명령을 실행합니다.

```text
/plugin marketplace update confluence-skills
```

**Codex:** marketplace를 새로고침하고 앱에서 플러그인 업데이트 상태를 확인합니다. 필요하면 새 세션에서 확인합니다.

```text
codex plugin marketplace upgrade confluence-skills
```

**Claude 웹/앱 및 수동 설치:** 최신 Release의 ZIP으로 교체합니다.

## 유지보수 및 배포

스킬 원본은 `plugins/confluence-docs/skills/confluence-doc-writer/`에 있습니다. 스킬 수정 후 두 플러그인 manifest의 버전을 동일하게 올립니다. ZIP에는 Git에 추적된 배포 파일만 들어가므로 새 공개 파일을 먼저 추가합니다. 개인 템플릿 폴더와 실제 설정은 ZIP에서도 제외합니다.

```text
git add .
python -m unittest discover -s tests
python scripts/package.py
git commit -m "Release 1.0.1"
git push origin main
git tag v1.0.1
git push origin v1.0.1
```

GitHub Actions가 검증 후 스킬 ZIP과 플러그인 ZIP을 Release에 첨부합니다. 태그가 manifest 버전과 다르면 배포를 중단합니다. Actions의 **Validate and release**에서 태그를 지정해 수동 실행할 수도 있습니다.

`dist/confluence-doc-writer.zip`은 Claude Skills/개인 스킬용, `dist/confluence-docs-plugin.zip`은 플러그인 패키지용입니다. 공식 디렉터리 등록은 이 자체 marketplace와 별도 제출 절차입니다.

자동 검증은 한국어 양식 선택, 로컬 양식 우선순위, 준비 상태의 누락·충돌, HTML 출력 검사와 배포 파일 제외 규칙을 포함합니다. 모델의 실제 대화·부분 수정 검토용 사례는 `tests/scenarios.md`에 있습니다. 실제 Claude/Codex의 동작과 대상 Confluence 편집기는 해당 환경에서 확인해야 합니다.

## 공식 문서

- [Claude marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude 업데이트](https://code.claude.com/docs/en/plugins/host-marketplace)
- [Claude Skills 업로드](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
- [Codex 플러그인 패키징과 marketplace](https://developers.openai.com/plugins/build/plugins)
- [Confluence 문서 가져오기 및 붙여넣기](https://support.atlassian.com/confluence-cloud/docs/import-content-into-confluence-cloud/)

## License

MIT
