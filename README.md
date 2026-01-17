# Resume-System

## 基于 Vue + SpringBoot + LangGraph 的简历分析系统

该系统为JLU毕业设计，个人开发的简易的简历分析系统。

------

### 功能

#### 1、用户登录、注册功能：

用户需要输入用户名和密码进行登录，同时需要选择登录的身份。可选的身份包括：求职者、招聘者。

#### 2、求职者用户的功能：

求职者用户在主页能够上传自己的简历；访问职位仓库；选择特定的职位与自己上传过的简历进行匹配度分析（由LangGraph实现的AI Workflow驱动）；为指定的上传过的简历推荐匹配度最高的几个职位（基于Embedding Model + Vector Database）；查询分析的历史记录（匹配度分析和推荐的结果都会保存到历史记录中）；使用“求职小助手”智能体，提供更多求职建议。

#### 3、招聘者用户的功能：

招聘者用户在主页能够发布新的职位；访问简历仓库；选择特定的简历与自己发布过的职位进行匹配度分析（由LangGraph实现的AI Workflow驱动）；为指定的发布过的职位推荐匹配度最高的几个简历（基于Embedding Model + Vector Database）；查询分析的历史记录（匹配度分析和推荐的结果都会保存到历史记录中）；使用“求职小助手”智能体（基于Agent + MCP，暂时没有启用memory机制，上下文仅在当前会话中生效，一旦重启会话上下文将重置），提供更多招聘建议和简历分析。

#### 4、简历与职位的管理（CRUD）：

用户有管理他们上传的简历或者发布的职位的功能。对于简历，用户可以上传、下载、删除的功能；对于职位，用户可以创建、查看、下载、删除。另外，简历目前仅支持文件上传且需为PDF格式，暂时没有手动输入创建简历的页面；职位可以选择手动输入，也可以选择上传文件，两种模式二选一，并且如果手动输入，下载功能将无效（因为创建过程中没有上传文件），而如果上传文件，那么手动输入框内的信息栏目在查看页面内显示为空（暂未构建AI分析结果写入对应栏目的功能）。

#### 5、表单的分页和筛选：

系统内所有表单都使用分页查询，并且配备有一些筛选条件设置框或按钮，实现带有过滤条件的分页查询。带有过滤的分页查询由Java后端的Mybatis-plus完成，分页和过滤的参数由前端传递（目前页面大小固定为10）。

------

### 依赖与环境

#### 1、Vue

前端界面需要使用Vue框架，同时使用了Vuetify组件库，需要安装node.js和npm（不过本人使用了pnpm替代npm进行包管理），具体依赖项查看 VueFrontend/package.json 。

#### 2、SpringBoot

Java后端使用SpringBoot框架，包管理器使用Maven，具体的依赖查看 JavaBackend/pom.xml 。另外需要注意：SpringBoot版本为2.7.12，使用的JDK版本为11，不要使用17、21或更新版本，会出现依赖不兼容！

#### 3、LangGraph

Python后端使用LangChain + LangGraph框架，同时由于Embedding Model采用本地部署，因此需要一点算力，最好主机要配有一张显卡，至于模型则自行下载配置。同时为了运行模型，需要安装PyTorch框架，且版本需要2.0.0以上。Python后端项目的配置文件为 PythonBackend/ResumeAnalyse/settings.json 。

另外提醒：PythonBackend/Resume_Data目录只是测试程序的样例数据，PythonBackend/ResumeAnalyse才是Python后端的源码。Python后端必须要在Linux或者WSL环境内运行，Windows下

#### 4、数据库和中间件

数据库采用MySQL，可以自行替换为其他的数据库，只是注意修改 JavaBackend/src/main/resources/application.yaml 文件配置即可。中间件包括Redis和RabbitMQ，具体配置也可以参考application.yaml（需要自行完善相关配置）。

------

### 运行项目

运行项目需要先启动数据库（比如MySQL）、Redis、RabbitMQ，之后运行后端程序JavaBackend和PythonBackend。其中JavaBackend可以选择使用 `mvn springboot:run` 命令直接运行，也可以使用 spring-boot-maven-plugin（**注意使用springboot适配的maven plugin，而不是默认的那个**）打包项目后再使用 `java -jar` 命令运行；PythonBackend 可以直接运行 PythonBackend/ResumeAnalyse/StartupServices.py ，需要注意的是，运行的时候需要输入 StartupServices.py 文件在你本机上的绝对路径，相对路径会出现 `no module named ResumeAnalyse` 的错误（这和源码中导入自定义Python文件的import语句有关，暂未完全修复）。最后启动Vue项目，在项目根目录内输入 `npm run dev` 即可运行项目，如果是本地开发，建议在 VueFrontend/vite.config.js 中将 `vueDevTools()` 取消注释，即可开启Vue自带的开发工具（会在渲染的页面底部显示，便于代码定位）；如果要部署前端还是建议使用 `npm run build` 打包Vue项目，再放到nginx服务器中部署运行。 

------

### 最后

如果您觉得这个项目有帮助，请给我点一个免费的小星星。谢谢！

If you think found project helpful, please give me a free star. Thank you!