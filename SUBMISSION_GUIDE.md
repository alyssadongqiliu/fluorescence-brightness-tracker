# JOSS 提交步骤指南

## ✅ 预检查完成
所有文件已准备就绪！现在按以下步骤提交。

---

## 第一步：创建 GitHub 仓库 (10分钟)

### 1. 在 GitHub 创建新仓库

1. 打开浏览器，访问：https://github.com/new
2. 填写信息：
   - **Repository name**: `fluotrack`
   - **Description**: `Automated multi-target fluorescence tracking with adaptive detection`
   - **Visibility**: ✅ **Public** (必须是公开的)
   - **不要**勾选 "Initialize this repository with:"
3. 点击 **Create repository**

### 2. 在本地初始化 Git 并推送

打开终端，执行以下命令：

```bash
# 进入项目目录
cd ~/Downloads/fluorescence-brightness-tracker

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: FluoTrack v0.1.0 for JOSS submission"

# 设置主分支
git branch -M main

# 添加远程仓库（替换为你的实际 GitHub 用户名）
git remote add origin https://github.com/alyssadongqiliu/fluotrack.git

# 推送到 GitHub
git push -u origin main
```

### 3. 创建版本标签

```bash
# 创建 v0.1.0 标签
git tag -a v0.1.0 -m "Version 0.1.0 - Initial JOSS submission"

# 推送标签
git push origin v0.1.0
```

**✅ 检查点：** 访问 https://github.com/alyssadongqiliu/fluotrack 确认文件都已上传

---

## 第二步：获取 Zenodo DOI (10分钟)

### 1. 链接 GitHub 到 Zenodo

1. 访问：https://zenodo.org/
2. 点击右上角 **Log in**，选择 **Log in with GitHub**
3. 授权 Zenodo 访问你的 GitHub 账户

### 2. 启用仓库归档

1. 登录后，访问：https://zenodo.org/account/settings/github/
2. 找到 `fluotrack` 仓库
3. 点击右边的 **ON** 按钮启用归档
4. 稍等几分钟，Zenodo 会自动为你的 v0.1.0 release 创建 DOI

### 3. 获取 DOI

1. 在 Zenodo GitHub 设置页面，点击你的仓库名称
2. 你会看到类似 `10.5281/zenodo.XXXXXXX` 的 DOI
3. 复制这个 DOI

### 4. 更新 README.md 的 DOI 徽章（可选）

编辑 README.md，将徽章更新为实际的 DOI：

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

然后提交：
```bash
git add README.md
git commit -m "Update Zenodo DOI badge"
git push
```

**✅ 检查点：** 你已经有了一个 Zenodo DOI

---

## 第三步：提交到 JOSS (5分钟)

### 1. 访问 JOSS 网站

打开：https://joss.theoj.org/

### 2. 开始提交

1. 点击页面顶部的 **"Submit a paper"** 按钮
2. 使用 GitHub 账户登录（如果还没登录）

### 3. 填写提交表单

填写以下信息：

```
Repository URL: 
https://github.com/alyssadongqiliu/fluotrack

Software Version:
v0.1.0

Archive DOI:
10.5281/zenodo.XXXXXXX  (填入你刚才获取的实际 DOI)

Software License:
MIT

```

### 4. 确认勾选项

勾选以下确认框：
- ✅ The software is open source
- ✅ The authors listed have contributed to the paper
- ✅ An Editor has not yet been assigned
- ✅ I understand the review process

### 5. 提交

点击 **"Submit my paper"** 按钮

**✅ 完成！** 🎉

---

## 第四步：等待审核

### 时间线：

1. **编辑分配** (1-2周)
   - JOSS 编辑会检查你的提交
   - 可能会有一些初步问题

2. **审稿人分配** (2-4周)
   - 通常会有 2 位审稿人
   - 他们会测试安装、运行代码、审阅论文

3. **审稿过程** (2-8周)
   - 审稿人会在 GitHub Issues 中提出问题和建议
   - 你需要及时回复（建议2周内）
   - 根据建议修改代码和论文

4. **接收** 🎉
   - 所有问题解决后，编辑会接收你的论文
   - 论文会发布在 JOSS 网站
   - 你会获得正式的 DOI 用于引用

### 如何响应审稿意见：

当审稿人提出问题时：

1. **礼貌回复**：感谢审稿人的建议
2. **逐条回应**：对每个问题都给出明确答复
3. **做出修改**：修改代码或论文
4. **引用提交**：在回复中引用你的 git commit

示例回复：
```markdown
Thank you for the helpful feedback!

1. ✅ Added more detailed docstrings (commit abc1234)
2. ✅ Expanded installation instructions in README (commit def5678)
3. Regarding the photobleaching algorithm, we chose linear regression 
   because it's more robust for noisy data. See the updated paper for 
   detailed explanation.
```

---

## 常见问题

### Q: 如果审稿人要求修改代码怎么办？

A: 
```bash
# 修改代码后
git add .
git commit -m "Fix: Add detailed docstrings as suggested by reviewers"
git push

# 如果需要新版本
git tag -a v0.1.1 -m "Version 0.1.1 - Address reviewer comments"
git push origin v0.1.1
```

### Q: 如果需要修改 paper.md 怎么办？

A: 直接在 GitHub 上编辑或本地修改后推送：
```bash
git add paper.md
git commit -m "Update paper.md based on reviewer feedback"
git push
```

### Q: 审稿过程中可以更新代码吗？

A: 可以！审稿过程就是为了改进软件。每次更新后在 GitHub Issue 中告知审稿人。

### Q: 如果被拒怎么办？

A: JOSS 的拒稿率很低。如果有问题，编辑会先让你修改。只要认真回应审稿意见，基本都能接收。

---

## 提交检查清单

在点击提交前，最后确认：

- [ ] GitHub 仓库是公开的
- [ ] 所有文件都已推送到 GitHub
- [ ] 已创建 v0.1.0 标签
- [ ] 已获取 Zenodo DOI
- [ ] paper.md 中 ORCID 正确
- [ ] paper.md 字数在 250-1000 之间
- [ ] paper.bib 引用完整
- [ ] README.md 有安装说明
- [ ] LICENSE 文件存在
- [ ] 测试文件存在且可以运行

---

## 联系方式

- **JOSS 帮助**: https://joss.readthedocs.io/
- **JOSS Gitter 聊天**: https://gitter.im/openjournals/joss
- **GitHub Issues**: https://github.com/openjournals/joss/issues

---

## 🎉 祝你提交顺利！

提交后记得：
1. 定期检查 GitHub Issues（开启邮件通知）
2. 及时回复审稿人
3. 保持积极友好的态度

Good luck! 加油！🚀
