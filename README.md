# Blog-manager

一个轻量的小工具用于规范 blog 的链接和引用图片url。

- blog 链接格式：8 位 16 进制数
- 引用图片 url： 8 位 16 进制数 / 8 位 16 进制数

## 使用方法

1. 复制 `_config.sample.yaml` 为 `_config.yaml`（如果你是 hexo 用户，将它加到原来的文件末尾）。

1. 将 main.py 复制到任意位置即可。

```yaml
# 自动管理 Blog 和引用图片并修复的小程序
# https://github.com/Rickyxrc/blog-manager

blogmanager:
  url_slug: postSlug                 # front-matter 中控制 url 的项目
  blog_path: P:\ath\to\markdown\root # Markdown 文件的根目录（绝对路径）
  image_path: P:\ath\to\image\root   # 图片的根目录（绝对路径）
  image_base_url: https://path-to-image-root # 图片访问的根目录
  commands:
    blog:
      path: # 命令执行位置（绝对路径）
      precommit: git diff                    # 显示 Blog 差异
      commit: git commit && git push         # 提交 Blog 更改
    image:
      path: # 命令执行位置（绝对路径）
      precommit: rclone sync . cdn:/blog --dry-run # 显示图片差异
      commit: rclone sync . cdn:/blog              # 提交图片更改
    other_commit: # 可以添加任意多项，但是必须要有 path 项和 commit 项。
      path: ...
      commit: ...
```
