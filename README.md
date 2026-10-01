# Confluence Skills

Claude와 Codex에서 Confluence 문서를 작성하는 스킬과 자체 플러그인 marketplace입니다.

기술 설계서, 운영 절차서, 회의록, 장애 보고서를 **붙여넣기용 HTML + 수정용 Markdown**으로 만듭니다. Confluence 연결이나 외부 라이브러리가 필요 없는 지침형 스킬입니다.

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

스킬 원본은 `plugins/confluence-docs/skills/confluence-doc-writer/`에 있습니다. 스킬 수정 후 두 플러그인 manifest의 버전을 동일하게 올립니다.

```text
python scripts/package.py
git add .
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
