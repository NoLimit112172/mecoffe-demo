# MeCoffe 校园沙盘：公开示例

在线演示：<https://NoLimit112172.github.io/mecoffe-demo/>

不需要登录、API 密钥或启动本地后端。点击“播放”，查看人物走到咖啡店、购买后返回，以及示例广告、晒单和评论的传播。支持暂停、倍速、按天跳转、30 天重播和人物关注关系查看。

## 数据说明

本仓库的全部人物、属性、关系和行为均为独立生成的合成示例，用于展示界面与交互。100 个主体包含 2 个虚构商家、70 名本科生、20 名研究生和 8 名教师；姓名使用“本科生01”等通用编号。关注网络和脚本通过固定种子独立生成。

该演示不包含团队私有画像、原始运行记录、历史销量或研究报告。演示金额、价格和传播结果属于示例规则，不是模型的新实验结果或现实预测。

## 本地运行

需要 Node.js 18+：

```sh
npm ci
npm run dev
```

打开终端打印的 `/mecoffe-demo/` 地址。构建静态网站：

```sh
npm run build
npm run preview
```

## 发布

`main` 分支通过 GitHub Actions 构建 `dist/` 并发布到 GitHub Pages；发布源选择 GitHub Actions。网站挂在 `/mecoffe-demo/` 子路径，运行数据与图集均使用相同前缀。

发布流程参考 [Vite 静态部署](https://vite.dev/guide/static-deploy)和 [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 来源与许可证

前端场景程序及美术图集沿用 YuLan-OneSim 的相关实现和素材，按 Apache License 2.0 使用。参见 `NOTICE.md` 和 `YULAN_LICENSE`。本公开项目仅保留沙盘所需的前端程序与图集。
