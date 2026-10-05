# 网站更新指南

这个网站发布在 `https://haoran-horace-zhu.github.io`。修改 `main` 分支后，GitHub Actions 会自动构建并发布，通常几分钟内上线。

## 常用修改位置

- 首页简介、教育和研究方向：`_pages/about.md`
- 论文与预印本：`_bibliography/papers.bib`
- CV 页面内容：`_data/cv.yml`
- 近期动态：`_news/`
- 学术活动：`_pages/calender.md`
- 邮箱、Scholar、ORCID、GitHub 等链接：`_config.yml`
- 网站颜色和版式：`_sass/_custom.scss`

## 添加一篇论文

在 `_bibliography/papers.bib` 顶部加入一条 BibTeX 记录。合作者写入 `author`，同时把除 Haoran Zhu 以外的作者写入 `coauthors`，供网页显示。

```bibtex
@article{Example2026,
  author={Collaborator, Alice and Zhu, Haoran},
  coauthors={Alice Collaborator},
  title={Paper title},
  journal={Preprint},
  year={2026},
  arxiv={2601.00001},
  bibtex_show={true}
}
```

如果论文已经发表，把 `journal` 改为期刊名称，并补充 `volume`、`number`、`pages` 和不带网址前缀的 `doi`。

## Notes and results

Research 页面在 Preprints 后保留了 **Notes and results (not intended for publication)** 栏目，不放占位文章。

以后加入经确认可以公开的文章时，在 `_bibliography/papers.bib` 中使用 `entry_kind={note}`。标题保持普通文字；Abstract、PDF 和 Bib 沿用现有按钮。填写可选的 `background` 字段后，会出现 Background 按钮，点击在该条目下面展开，不跳转到档案页。

```bibtex
@misc{ExampleNote2026,
  author={Zhu, Haoran},
  title={Note title},
  year={2026},
  entry_kind={note},
  abstract={The abstract of the note.},
  pdf={approved-note.pdf},
  background={A short account of how the note came about.},
  bibtex_show={true}
}
```

`background` 支持 Markdown，可写实际的写作经过、完成时间和后续想法；不必每篇解释为什么不发表。只记录作者确认的事实，不以文件上传日期代替稿件完成日期。若有合作者，使用上文的 `coauthors` 字段。`background` 不会出现在 BibTeX 引用中。不要将原有 Publications 或 Preprints 自动移入此栏目，也不要把本地未公开的稿件或 PDF 随其他更新一起提交。

## 发布检查

提交后打开仓库的 **Actions → Deploy site**。绿色勾表示发布成功；红色叉表示构建失败。网站内容更新时只需要维护上述个人文件，不需要改主题模板。
