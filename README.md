# Confluence Skills

Claude와 Codex에서 Confluence 문서를 작성하는 스킬과 자체 플러그인 marketplace입니다.

기술 설계서, 운영 절차서, 회의록, 장애 보고서를 **붙여넣기용 HTML + 수정용 Markdown**으로 만듭니다. 필요한 다이어그램은 PNG와 개별 도형을 편집할 수 있는 `.drawio` 원본으로 제공합니다. 문서 작성 자체는 Confluence 연결이 필요 없는 지침형 스킬입니다. PNG 렌더링에는 사용 환경의 로컬 렌더링 도구가 필요하며, 없는 경우 원본과 내보내기 안내를 제공합니다.

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

요청에서 지정한 양식이 기본 설정보다 우선합니다. 양식의 목차·표·고정 문구를 유지하며 자료가 없는 값은 `확인 필요`로 표시합니다. 지정 파일을 찾을 수 없으면 임의의 양식으로 대체하지 않습니다.

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

기본 산출물은 `diagrams/process-flow.drawio`와 `diagrams/process-flow.png`입니다. HTML에 PNG 미리보기를 배치하고, 원본은 별도로 제공합니다. Mermaid를 명시하면 `.mmd` 원본도 사용할 수 있지만 draw.io 원본과 같은 형식은 아닙니다.

**Confluence에서 편집:** 본문을 붙여넣은 다음 그림 위치에 draw.io Diagram 요소를 추가하고 `.drawio` 원본을 가져옵니다. 설치된 draw.io 앱에서 도형·문구·연결선을 수정합니다. 앱이 없으면 PNG를 첨부하고 원본을 별도로 편집해 다시 내보냅니다. HTML을 붙여넣는 것만으로 draw.io 요소가 생성되지는 않습니다.

문서와 `diagrams/` 폴더를 함께 보관하면 로컬 HTML에서 상대 경로 이미지가 표시됩니다. PNG 생성 도구가 없는 환경에서는 원본만 제공하고 미생성 상태를 명시합니다. 회사 자료를 원격 렌더링 서비스에 자동 전송하지 않습니다.

매크로는 패널·접기·목차 등 삽입 위치와 안내를 제공하며, 기본 붙여넣기 방식에서 자동 생성된다고 보장하지 않습니다.

```text
Confluence 문서 작성 스킬을 사용해 report 템플릿으로 작성해줘.
다이어그램은 이해에 도움이 될 때만 넣고 PNG와 편집용 draw.io 원본을 제공해줘.
```

## 문서 사용

1. 메모나 파일을 제공하고 문서 작성을 요청합니다.
2. 생성된 HTML을 브라우저에서 엽니다.
3. 제목은 Confluence 제목 필드에 입력합니다.
4. 제목 아래 **보이는 본문**을 복사해 Confluence 본문에 일반 붙여넣기합니다.
5. 표, 코드 줄바꿈, 링크를 확인합니다. 필요한 이미지는 별도로 첨부합니다.

HTML 소스나 Markdown 원문을 그대로 붙여넣는 방식은 아닙니다. 편집기 버전에 따라 서식이 달라질 수 있으며 페이지를 자동 게시하지 않습니다.

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

현재 검증은 manifest 이름·버전·경로, 참조 파일, ZIP 무결성 중심입니다. 실제 Claude/Codex의 문서 생성과 대상 Confluence 편집기의 붙여넣기는 해당 환경에서 확인해야 합니다.

## 공식 문서

- [Claude marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude 업데이트](https://code.claude.com/docs/en/plugins/host-marketplace)
- [Claude Skills 업로드](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
- [Codex 플러그인 패키징과 marketplace](https://developers.openai.com/plugins/build/plugins)
- [Confluence 문서 가져오기 및 붙여넣기](https://support.atlassian.com/confluence-cloud/docs/import-content-into-confluence-cloud/)

## License

MIT
