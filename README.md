# Education 3D Models

超级实验室 VR 的教学模型库。超过 100 MB 的单个模型或会让 APK 超过 300 MB 的模型使用 GitHub Releases 分发。课堂档保留在应用内，高精度动物细胞使用按需下载。已下载的模型可以离线重复使用。

## 模型来源

- Animal cell 2.0 – annotated in English，由 montanna 创作，[原作](https://sketchfab.com/3d-models/animal-cell-20-annotated-in-english-0d9f7f4257224975b2ef83a283709b2f)。高精度档保留原三角形，合并静态网格、归一化尺寸。课堂档另外减面。
- Formation of phi Molecular Orbitals，由 Vera4art 创作，[原作](https://sketchfab.com/3d-models/formation-of-phi-molecular-orbitals-5f57d18ef46a4bb885f27df32f05e608)。Quest 将四组示意中的输入与产物分别提取，保留原作颜色，用于接触组合演示。

两项原作均采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。杂化轨道方向示意由项目另行绘制。

## 上传与自动更新

教师扩展的「上传模型到模型库」可以发布一个自包含文件，选择低、中、高中的一个或多个档位。同名同档更新会沿用目录条目。把模型手动提交到 main 分支也会触发转换，默认生成三档。支持 GLB、内嵌资源的 glTF、FBX、OBJ、STL、PLY 和 DAE。需要材质和外部贴图时，推荐先打包为 GLB。

转换在 GitHub Actions 中进行。当前面数上限暂定 15,000、40,000 和 75,000 个三角形，贴图最长边分别为 1024、2048 和 4096。成功后更新 catalog.json，Quest 打开「实验道具 → 云端模型库」会立即检查更新，持续打开时每分钟复查。教师分享的模型和 Sketchfab 在线展示统一出现在云端模型库。特殊物品分类只列出应用内置道具。可下载模型由学生点选下载。模型卡片右下角的垃圾桶仅删除该档的本地缓存。
