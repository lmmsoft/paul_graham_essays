---
title: "自底向上编程"
original_title: "Programming Bottom-Up"
author: "Paul Graham"
translator: "deepseek-ai/DeepSeek-V3 (SiliconFlow)"
translate_date: "2025-07-14"
source_file: "Programming Bottom-Up.md"
---

# 自底向上编程

| | [](index.html)  

|  

1993年  

（本文节选自《On Lisp》序言）  

程序的功能单元不应过于庞大，这一编程风格原则由来已久。当某个组件膨胀到难以理解的程度时，它就会变成一团隐匿错误的混沌体，如同大都市藏匿逃犯般容易。这样的软件将难以阅读、测试和调试。  

根据这一原则，大型程序必须被拆解，且规模越大，划分越需细致。如何划分程序？传统方法称为_自顶向下设计_：即先确定"程序需完成这七项功能，故划分为七个主要子程序。第一个子程序需实现四项功能，因此它自身又包含四个子程序"，如此层层递进，直至整个程序达到合适的粒度——每个部分既能实现实质功能，又可作为独立单元被理解。  

资深的Lisp程序员采用不同的划分方式。除自顶向下设计外，他们遵循可称为_自底向上设计_的原则——通过改造语言来适应问题。在Lisp中，你不仅自上而下地用语言编写程序，更自下而上地为程序构建语言。编程时你可能会想"要是Lisp有某某操作符就好了"，于是你动手实现它。随后你会发现这个新操作符能简化程序其他部分的设计，如此往复。语言与程序共同进化。如同交战国的边境线，语言与程序的边界被不断重新划定，最终沿着问题的自然疆界——那些山脉与河流——稳定下来。最终你的程序会看起来像是为其量身定制的语言。当语言与程序完美契合时，产出的代码将清晰、简洁且高效。  

值得强调的是，自底向上设计并非仅以不同顺序编写相同程序。采用这种方法时，你最终得到的往往是另一个程序。不同于单一的整体式程序，你会获得一个包含更多抽象操作符的增强语言，以及用该语言编写的更精简程序。这好比用拱门替代了过梁。  

典型代码中，当你抽离出那些纯属簿记的部分后，剩余内容会大幅缩减；语言构建得越高层，从顶层向下追溯的距离就越短。这带来诸多优势：

1. 通过让语言承担更多工作，自底向上设计能产出更精简、更灵活的程序。较短的程序无需被拆分成过多组件，更少的组件意味着程序更易于阅读或修改。组件减少也意味着组件间的连接更少，从而降低出错概率。正如工业设计师努力减少机器中的活动部件，经验丰富的Lisp程序员运用自底向上设计来降低程序的规模和复杂度。

2. 自底向上设计促进代码复用。当你编写两个及以上程序时，为首个程序编写的许多工具函数在后续程序中同样适用。一旦积累了大量基础工具集，编写新程序所需精力可能仅为从原始Lisp起步的零头。

3. 自底向上设计提升程序可读性。这类抽象实例要求读者理解通用运算符；而函数式抽象实例则要求理解专用子程序。[1]

4. 由于这种设计促使你持续关注代码中的模式，自底向上工作有助于厘清程序设计思路。若程序中两个相距较远的组件形式相似，你会自然注意到这种相似性，并可能以更简洁的方式重构程序。

在非Lisp语言中，自底向上设计也能实现到某种程度。任何库函数的存在都体现着这种设计。但Lisp在这方面赋予开发者更强大的能力，语言扩展在Lisp编程风格中占据更核心地位——这种差异如此显著，使得Lisp不仅是独特的语言，更代表着截然不同的编程范式。

诚然，这种开发风格更适合小团队编写的程序。但与此同时，它拓展了小团队的能力边界。在《人月神话》中，弗雷德里克·布鲁克斯提出程序员群体的生产力并不随规模线性增长。随着团队扩大，个体程序员的生产力反而下降。而Lisp编程经验为这一定律提供了更乐观的表述：随着团队规模缩小，个体程序员的生产力将提升。相对而言，小团队的优势恰恰在于其"小"。当小团队充分运用Lisp提供的技术时，他们能取得[压倒性胜利](avg.html)。

**新动态**：[免费下载《On Lisp》](onlisptext.html)。

* * *

[1] "但若不理解所有新工具函数，就无法读懂程序。"此类观点通常存在谬误，具体分析参见第4.8节。

* * *