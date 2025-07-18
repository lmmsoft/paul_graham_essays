---
title: "关于语言设计的五个问题"
original_title: "Five Questions about Language Design"
author: "Paul Graham"
translator: "deepseek-ai/DeepSeek-V3 (SiliconFlow)"
translate_date: "2025-07-14"
source_file: "Five Questions about Language Design.md"
---

# 关于语言设计的五个问题

| | [](index.html)  

|  

2001年5月  

（这是我在2001年5月10日麻省理工学院关于编程语言设计的专题讨论会上准备的笔记。）  

  

**1. 编程语言是为人服务的。**  

编程语言是人们与计算机交流的方式。计算机其实并不在乎使用哪种语言，只要语言没有歧义就行。我们之所以需要高级语言，是因为人类无法直接处理机器语言。编程语言的意义在于保护我们脆弱的人类大脑不被大量细节淹没。  

建筑师知道，某些设计问题比其他问题更关乎人性。桥梁设计是最纯粹、最抽象的设计问题之一，主要任务是用最少的材料跨越给定的距离。而另一端的极端则是椅子设计。椅子设计师必须花时间考虑人类的臀部。  

软件设计同样如此。设计网络数据路由算法是一个优美而抽象的问题，就像设计桥梁。而设计编程语言则像设计椅子：核心在于应对人类的弱点。  

大多数人都不愿承认这一点。设计具有数学美感的系统听起来比迎合人类弱点要吸引人得多。数学美感确实有其价值：某些形式的美感能让程序更易理解。但美感本身并非目的。  

当我说语言必须针对人类弱点设计时，并非指要为糟糕的程序员设计。事实上我认为应该为[最优秀的程序员](design.html)设计，但即使最优秀的程序员也有局限。没人会愿意用所有变量都是带整数下标的字母x的语言编程。  

**2. 为自己和朋友设计。**  

纵观编程语言的历史，许多最优秀的语言都是设计者为自己使用而创造的，而许多最糟糕的语言则是为他人设计的。  

为他人设计的语言总是面向特定群体：那些不如语言设计者聪明的人。因此你会得到一种居高临下的语言。COBOL是最极端的例子，但许多语言都弥漫着这种气息。  

这与语言的抽象程度无关。C语言相当底层，但它是设计者为自己所用而创造的，这正是黑客们喜爱它的原因。  

为糟糕程序员设计语言的理由是：糟糕程序员比优秀程序员多得多。这或许没错。但那少数优秀程序员编写的代码占比却大得不成比例。  

我感兴趣的问题是：如何设计出顶尖黑客会喜爱的语言？我认为这等同于"如何设计优秀的编程语言"，但即便两者不同，这至少是个有趣的问题。  

**3. 给予程序员最大限度的控制权。**  

许多语言（尤其是为他人设计的语言）带着保姆心态：它们试图阻止你做一些它们认为对你不利的事情。我推崇相反的方法：尽可能给予程序员更多控制权。  

当我初次学习Lisp时，最吸引我的是它把我视为平等的伙伴。在我之前学过的其他语言中，语言本身和用该语言编写的程序是截然分离的。但在Lisp中，我编写的函数和宏与构成语言本身的那些完全平等。我可以按需重写语言。这种吸引力与开源软件如出一辙。  

**4. 追求简洁。**  

简洁被低估甚至轻视。但若你洞察黑客的内心，会发现他们真心热爱简洁。你多少次听黑客满怀深情地谈起，比如在APL中，他们用短短几行代码就能实现惊人的功能？我认为真正聪明人真正热爱的事物都值得关注。  

几乎所有能让程序更短小的改进都是好的。应该提供大量库函数；所有能隐式表达的就应该隐式表达；语法应该简洁到极致；甚至连命名都应该简短。  

不仅程序要简短，手册也应该薄如蝉翼。手册中很大篇幅被用于解释、限制、警告和特殊情况。如果强迫自己精简手册，最理想的情况是通过修复语言中那些需要大量解释的部分来实现。  

**5. 承认编程的本质。**  

许多人希望编程是数学，或者至少像自然科学。我认为编程更像建筑学。建筑学与物理学相关，因为建筑师必须设计不会倒塌的建筑，但建筑师的真正目标是创造伟大的建筑，而非发现静力学规律。  

黑客热爱的是创造伟大程序。我认为，至少在我们心中，必须记住编写伟大程序是值得钦佩的事，即使这项工作无法轻易转化为研究论文这种传统的学术成果。从智力层面看，设计程序员喜爱的语言与设计体现某个可发表论文概念的糟糕语言同样有价值。  

  

**1. 如何组织大型库？**  

库正成为编程语言日益重要的组成部分。它们也变得越来越庞大，这可能是危险的。如果寻找能实现需求的库函数比自己编写耗时更长，那么这些代码除了让手册变厚外毫无意义。（Symbolics手册就是例证。）因此我们必须研究库的组织方式。理想情况是设计出能让程序员凭直觉猜到正确库调用的库。  

**2. 人们真的害怕前缀语法吗？**  

这是个开放性问题，我思考多年仍无答案。除了数学表达式，前缀语法对我来说非常自然。但Lisp不受欢迎可能仅仅因为语法陌生。如果确实如此，是否要为此做出改变则是另一个问题。

**3. 基于服务器的软件需要什么？**

我认为未来二十年最令人兴奋的新应用程序大多将是基于网络的应用，即那些驻留在服务器上、通过网页浏览器与用户交互的程序。而编写这类程序，我们可能需要一些新的工具。

首先，我们需要支持基于服务器的应用程序发布新方式。与桌面软件每年发布一两个大版本不同，服务器应用以一系列小变更的形式持续发布，每天可能有多达五到十次更新。通常所有用户都会始终使用最新版本。

正如程序需要设计为可调试的，服务器软件同样需要设计为可变更的——你必须能轻松修改它，或至少能判断哪些改动是轻微的，哪些是重大的。

另一个出人意料但对服务器软件可能有用的概念是"续体"（continuations）。在无状态的网络会话中，你可以采用类似"续体传递风格"的技术来实现[子程序](lwba.html)的效果。如果成本可控，真正的续体机制或许值得引入。

**4. 还有哪些新抽象等待发现？**

这或许有些理想化，但我个人非常渴望能发现一种新的抽象机制——其重要性堪比一等函数、递归甚至关键字参数。虽然这类突破并不常见，但我始终在探寻。

**1. 语言选择自由**

过去编写应用就意味着开发桌面软件，而桌面软件存在强烈倾向：必须使用与操作系统相同的语言开发。因此十年前，软件开发几乎等同于用C语言编程。久而久之形成了一种传统：应用软件不得使用非常规语言，这种观念甚至渗透到管理者和风投等非技术群体中。

服务器软件彻底颠覆了这一模式。你可以自由选择任何编程语言，尽管目前大多数人（尤其是管理者和风投）尚未意识到这一点。少数黑客明白这个道理，这正是我们还能听到Perl、Python等新兴语言的原因——它们并非因开发Windows应用而闻名。

这对语言设计者意味着：我们的工作终于可能迎来真正的受众。

**2. 性能优化源于分析器**

语言设计者（至少实现者）热衷于编写能生成高效代码的编译器。但真正提升用户体验的速度并非来源于此。Knuth早已指出：性能瓶颈往往只存在于少数关键路径，而这些路径无法凭空猜测。分析器才是答案所在。

语言设计者正在解决错误的问题。用户不需要基准测试跑得多快，他们需要的是能精准定位程序瓶颈的语言工具。这才是实践中性能提升的来源。如果将编译器优化的时间抽出一半用于开发优秀的分析器，或许会带来更显著的整体收益。

**3. 语言设计需要应用场景驱动**

这或许不是铁律，但最优秀的语言往往伴随着特定应用场景共同演化：C语言诞生于系统编程需求，Lisp的部分发展动力来自符号微分计算——McCarthy在1960年首篇Lisp论文中就迫不及待地开始编写微分程序。

如果应用场景涉及解决新问题则更为理想，这会推动语言产生程序员真正需要的新特性。我个人感兴趣的是打造适合服务器应用开发的语言。

[讨论环节中Guy Steele也强调这一点，并补充建议：除非专门用于编译器开发，否则语言的应用场景不应局限于编写自身的编译器。]

**4. 语言必须擅长编写临时程序**

临时程序指为特定任务快速编写的简易程序。仔细观察会发现，许多严肃的大型程序最初都是临时程序。甚至可能大多数软件都始于临时程序阶段。因此要打造通用编程语言，必须首先擅长编写临时程序——这是多数软件的雏形阶段。

**5. 语法与语义的关联**

传统观念认为语法与语义完全分离。但令人惊讶的是，它们可能存在深层联系。Robert Morris曾指出：在中缀语法语言中，操作符重载的价值更为显著。在前缀语法语言中，任何自定义函数本质上都是操作符；而在中缀语言中，重载操作符与函数调用的视觉差异极大。

**1. 新编程语言的复兴**

1970年代曾掀起设计新语言的浪潮，近期虽式微，但服务器软件将重启这一趋势。当语言选择不再受限时，只要出现真正优秀的语言设计，就有人愿意冒险尝试。

**2. 分时系统的回归**

Richard Kelsey在上次讨论中提出分时理念将复兴，我完全赞同。与微软的判断类似，大量计算将从桌面转移到远程服务器——分时模式正在回归。这需要语言层面的支持，例如Richard和Jonathan Rees已在Scheme 48中实现了大量进程调度工作。

**3. 效率重现重要性**

当人们开始讨论字节码（暗示计算资源过剩）时，似乎计算机性能已足够强大。但服务器软件将改变这一认知：硬件成本需要真实支付，单机承载用户数直接决定资本回报率。

因此效率再次成为关键，尤其在I/O性能方面——这正是服务器应用的核心瓶颈。当前Sun与微软的"字节码之战"更多是商业策略，字节码本身未必是最优解。若这个战场最终被绕过，倒不失为趣事。

**1. 客户端终将式微**

我的预测是：绝大多数应用将采用纯服务器架构。假设所有用户都安装特定客户端，就如同假设全社会绝对诚实——虽然便利，但绝不可行。

未来将涌现各种具备基础网络功能的设备，但唯一可确定的共性就是支持简单HTML和表单。手机浏览器？PDA通话功能？黑莓大屏？游戏手表？与其猜测设备形态，不如将所有[智能集中于服务器](road.html)——这才是稳健之选。

**2. 面向对象编程的反思**

尽管存在争议，但我认为面向对象编程被过度神话。它对窗口系统、仿真、CAD等需要特定数据结构的应用是优秀模型，但不该成为编程的普适范式。

大公司青睐面向对象的部分原因在于它制造了大量"看似专业"的代码——本该用整数列表简单表达的概念，被包装成充满样板代码的类结构。

面向对象的方法虽能模拟一等函数的部分功能，但对Lisp程序员而言这早已过时。拥有真正的一等函数时，你可以根据任务灵活运用，而非强迫所有逻辑适配类与方法的框架。

这对语言设计的启示是：不应深度绑定面向对象范式。或许更好的方案是提供更通用的底层机制，让人们通过库来实现各类对象系统。

**3. 委员会设计的陷阱**

委员会设计语言不仅是众所周知会导致臃肿和不一致，更深层的危机在于规避风险。个人主导时敢于尝试的创新，在委员会决策中永远无法通过。

但语言设计是否需要冒险？许多人认为应当遵循传统智慧。然而所有创造性活动的回报都与风险成正比，语言设计何尝例外？

---

[日语译本](http://d.hatena.ne.jp/lionfan/20070215)

***  
  
---