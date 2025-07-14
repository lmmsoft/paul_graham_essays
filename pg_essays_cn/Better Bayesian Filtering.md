---
title: "更好的贝叶斯过滤"
original_title: "Better Bayesian Filtering"
author: "Paul Graham"
translator: "deepseek-ai/DeepSeek-V3 (SiliconFlow)"
translate_date: "2025-07-14"
source_file: "Better Bayesian Filtering.md"
---

# 更好的贝叶斯过滤

| | [](index.html)  

|  

2003年1月  

（本文是我在2003年反垃圾邮件大会上的演讲内容，描述了我对《反垃圾邮件计划》所述算法的改进工作及未来规划。）  

我要分享的第一个发现是研究论文的惰性评估算法：只需写出你想写的内容且不引用任何前人工作，愤怒的读者自会发来你本该引用的所有文献。这个算法是我在《反垃圾邮件计划》[1]被Slashdot转载后悟出的。  

垃圾邮件过滤属于文本分类的子领域，这个学科已相当成熟。但最早的贝叶斯垃圾邮件过滤论文似乎都出现在1998年的同场会议上：一篇来自Pantel和Lin[2]，另一篇来自微软研究院团队[3]。  

得知这些研究时我有些惊讶。既然四年前就有人研究贝叶斯过滤，为何没有普及？读完论文后我找到了答案。Pantel和Lin的过滤器效果较好，但仅能拦截92%的垃圾邮件，且有1.16%的误判率。  

而我编写的贝叶斯过滤器实现了99.5%的垃圾邮件拦截率和低于0.03%的误判率[4]。当相同实验得出迥异结果时总是令人不安，尤其这两组数据可能导致相反结论。虽然用户需求各异，但对多数人而言，92%拦截率配1.16%误判率意味着过滤方案不可行，而99.5%拦截率配0.03%误判率则完全可行。  

为何结果差异如此之大？虽未复现Pantel和Lin的实验，但从论文中我发现了五个可能原因：  

首先，他们的训练数据量过少——仅160封垃圾邮件和466封正常邮件。这种数据规模下过滤性能应仍在上升期，因此其数据甚至不足以准确衡量其算法表现，更不用说整体贝叶斯过滤效果。  

但最关键的区别可能是他们忽略了邮件头。这对反垃圾邮件开发者来说是个反常决定。有趣的是，我最初编写的过滤器也忽略了邮件头——因为当时对邮件头知之甚少，觉得它们充满杂乱信息。这给过滤器开发者上了重要一课：不要忽视任何数据。这个教训看似显而易见，我却多次重蹈覆辙。  

第三，Pantel和Lin对词汇进行了词干提取（如将"mailing"和"mailed"都归为"mail"）。这可能是受限于小规模语料库的妥协，但实属过早优化。  

第四，他们采用不同的概率计算方式：使用全部词汇特征，而我仅选取15个最显著特征。使用全部特征会导致漏判长篇垃圾邮件（比如那些先讲述人生故事再推销传销项目的邮件）。这种算法也容易被攻击：只需添加大段随机文本就能稀释垃圾词汇特征。  

最后，他们没有针对误判进行优化。我认为所有垃圾邮件过滤算法都应提供调节旋钮，允许用户通过降低过滤率来减少误判。我的解决方案是对正常邮件中的词汇特征进行双倍计数。  

将垃圾邮件过滤简单视作文本分类问题并不明智。虽然可以运用文本分类技术，但解决方案必须体现电子邮件的特殊性——尤其是垃圾邮件。邮件不仅是文本，还具有结构特征；过滤不仅是分类，更因误判代价远高于漏判而需区别对待；错误来源不仅是随机偏差，还包括刻意对抗过滤器的垃圾邮件发送者。  

**词汇特征**  

Slashdot事件后，我还了解到Bill Yerazunis的[CRM114][5]项目。它完美反驳了我刚提出的设计原则——这个纯粹的文本分类器甚至不知道自己用于反垃圾邮件，却实现了近乎完美的过滤效果。  

理解CRM114原理后，我意识到从单词级过滤转向此类方法是大势所趋。但我想先探索单词级过滤的极限——结果证明其潜力远超预期。  

我的主要突破在于更智能的词汇切分技术。针对当前垃圾邮件，我的过滤效果已接近CRM114。这些技术与Bill的方案大多互补，最佳解决方案或许需要二者结合。  

《反垃圾邮件计划》采用极简的词汇定义：字母、数字、连字符、撇号和美元符号视为组成字符，其余皆作分隔符，且忽略大小写。  

现在我的词汇定义更为复杂：  
1. 保留大小写

2. 感叹号是构成性字符。


3. 当句号和逗号出现在两个数字之间时，它们被视为构成性字符。这使得IP地址和价格能保持完整。


4. 类似$20-25的价格区间会生成两个标记：$20和$25。


5. 出现在“收件人”、“发件人”、“主题”和“返回路径”行或网址内的标记会进行相应标注。例如，主题行中的“foo”会变成“Subject*foo”（星号可以是任何不被允许作为构成性字符的符号）。

这些措施增加了过滤器的词汇量，使其更具辨别力。例如，在当前过滤器中，主题行中的“free”标记的垃圾邮件概率为98%，而正文中相同标记的垃圾邮件概率仅为65%。

以下是当前部分概率值[6]：

Subject*FREE      0.9999
free!!            0.9999
To*free           0.9998
Subject*free      0.9782
free!             0.9199
Free              0.9198
Url*free          0.9091
FREE              0.8747
From*free         0.7636
free              0.6546

在“Plan for Spam”过滤器中，所有这些标记的概率都相同，为0.7602。该过滤器能识别约23,000个标记，而当前版本能识别约187,000个。

扩大标记范围的缺点是可能增加遗漏风险。将语料分散到更多标记上会产生与缩小语料相同的效果。例如，如果将感叹号视为构成性字符，最终可能无法获取带有七个感叹号的“free”的垃圾邮件概率，尽管已知仅带两个感叹号的“free”概率为99.99%。

对此的解决方案是我所称的“退化处理”。如果找不到标记的精确匹配，则将其视为不太具体的版本。我认为结尾的感叹号、大写字母以及出现在五个特定上下文之一中的标记会使标记更具体。例如，如果找不到“Subject*free!”的概率，就查找“Subject*free”、“free!”和“free”的概率，并取最偏离0.5的值。

以下是过滤器在主题行中看到“FREE!!!”但未找到其概率时会考虑的备选方案[7]：

Subject*Free!!!
Subject*free!!!
Subject*FREE!
Subject*Free!
Subject*free!
Subject*FREE
Subject*Free
Subject*free
FREE!!!
Free!!!
free!!!
FREE!
Free!
free!
FREE
Free
free

If you do this, be sure to consider versions with initial caps as well as all uppercase and all lowercase. Spams tend to have more sentences in imperative mood, and in those the first word is a verb. So verbs with initial caps have higher spam probabilities than they would in all lowercase. In my filter, the spam probability of ``Act'' is 98% and for ``act'' only 62%.  
  
If you increase your filter's vocabulary, you can end up counting the same word multiple times, according to your old definition of ``same''. Logically, they're not the same token anymore. But if this still bothers you, let me add from experience that the words you seem to be counting multiple times tend to be exactly the ones you'd want to.  
  
Another effect of a larger vocabulary is that when you look at an incoming mail you find more interesting tokens, meaning those with probabilities far from .5. I use the 15 most interesting to decide if mail is spam. But you can run into a problem when you use a fixed number like this. If you find a lot of maximally interesting tokens, the result can end up being decided by whatever random factor determines the ordering of equally interesting tokens. One way to deal with this is to treat some as more interesting than others.  
  
For example, the token ``dalco'' occurs 3 times in my spam corpus and never in my legitimate corpus. The token ``Url*optmails'' (meaning ``optmails'' within a url) occurs 1223 times. And yet, as I used to calculate probabilities for tokens, both would have the same spam probability, the threshold of .99.  
  
That doesn't feel right. There are theoretical arguments for giving these two tokens substantially different probabilities (Pantel and Lin do), but I haven't tried that yet. It does seem at least that if we find more than 15 tokens that only occur in one corpus or the other, we ought to give priority to the ones that occur a lot. So now there are two threshold values. For tokens that occur only in the spam corpus, the probability is .9999 if they occur more than 10 times and .9998 otherwise. Ditto at the other end of the scale for tokens found only in the legitimate corpus.  
  
I may later scale token probabilities substantially, but this tiny amount of scaling at least ensures that tokens get sorted the right way.  
  
Another possibility would be to consider not just 15 tokens, but all the tokens over a certain threshold of interestingness. Steven Hauser does this in his statistical spam filter [8]. If you use a threshold, make it very high, or spammers could spoof you by packing messages with more innocent words.  
  
Finally, what should one do about html? I've tried the whole spectrum of options, from ignoring it to parsing it all. Ignoring html is a bad idea, because it's full of useful spam signs. But if you parse it all, your filter might degenerate into a mere html recognizer. The most effective approach seems to be the middle course, to notice some tokens but not others. I look at a, img, and font tags, and ignore the rest. Links and images you should certainly look at, because they contain urls.  
  
I could probably be smarter about dealing with html, but I don't think it's worth putting a lot of time into this. Spams full of html are easy to filter. The smarter spammers already avoid it. So performance in the future should not depend much on how you deal with html.  
  
 **Performance**  
  
Between December 10 2002 and January 10 2003 I got about 1750 spams. Of these, 4 got through. That's a filtering rate of about 99.75%.  
  
Two of the four spams I missed got through because they happened to use words that occur often in my legitimate email.  
  
The third was one of those that exploit an insecure cgi script to send mail to third parties. They're hard to filter based just on the content because the headers are innocent and they're careful about the words they use. Even so I can usually catch them. This one squeaked by with a probability of .88, just under the threshold of .9.  
  
Of course, looking at multiple token sequences would catch it easily. ``Below is the result of your feedback form'' is an instant giveaway.  
  
The fourth spam was what I call a spam-of-the-future, because this is what I expect spam to evolve into: some completely neutral text followed by a url. In this case it was was from someone saying they had finally finished their homepage and would I go look at it. (The page was of course an ad for a porn site.)  
  
If the spammers are careful about the headers and use a fresh url, there is nothing in spam-of-the-future for filters to notice. We can of course counter by sending a crawler to look at the page. But that might not be necessary. The response rate for spam-of-the-future must be low, or everyone would be doing it. If it's low enough, it [won't pay](wfks.html) for spammers to send it, and we won't have to work too hard on filtering it.  
  
Now for the really shocking news: during that same one-month period I got _three_ false positives.  
  
In a way it's a relief to get some false positives. When I wrote ``A Plan for Spam'' I hadn't had any, and I didn't know what they'd be like. Now that I've had a few, I'm relieved to find they're not as bad as I feared. False positives yielded by statistical filters turn out to be mails that sound a lot like spam, and these tend to be the ones you would least mind missing [9].  
  
Two of the false positives were newsletters from companies I've bought things from. I never asked to receive them, so arguably they were spams, but I count them as false positives because I hadn't been deleting them as spams before. The reason the filters caught them was that both companies in January switched to commercial email senders instead of sending the mails from their own servers, and both the headers and the bodies became much spammier.  
  
The third false positive was a bad one, though. It was from someone in Egypt and written in all uppercase. This was a direct result of making tokens case sensitive; the Plan for Spam filter wouldn't have caught it.  
  
It's hard to say what the overall false positive rate is, because we're up in the noise, statistically. Anyone who has worked on filters (at least, effective filters) will be aware of this problem. With some emails it's hard to say whether they're spam or not, and these are the ones you end up looking at when you get filters really tight. For example, so far the filter has caught two emails that were sent to my address because of a typo, and one sent to me in the belief that I was someone else. Arguably, these are neither my spam nor my nonspam mail.  
  
Another false positive was from a vice president at Virtumundo. I wrote to them pretending to be a customer, and since the reply came back through Virtumundo's mail servers it had the most incriminating headers imaginable. Arguably this isn't a real false positive either, but a sort of Heisenberg uncertainty effect: I only got it because I was writing about spam filtering.  
  
Not counting these, I've had a total of five false positives so far, out of about 7740 legitimate emails, a rate of .06%. The other two were a notice that something I bought was back-ordered, and a party reminder from Evite.  
  
I don't think this number can be trusted, partly because the sample is so small, and partly because I think I can fix the filter not to catch some of these.  
  
False positives seem to me a different kind of error from false negatives. Filtering rate is a measure of performance. False positives I consider more like bugs. I approach improving the filtering rate as optimization, and decreasing false positives as debugging.  
  
So these five false positives are my bug list. For example, the mail from Egypt got nailed because the uppercase text made it look to the filter like a Nigerian spam. This really is kind of a bug. As with html, the email being all uppercase is really conceptually _one_ feature, not one for each word. I need to handle case in a more sophisticated way.  
  
So what to make of this .06%? Not much, I think. You could treat it as an upper bound, bearing in mind the small sample size. But at this stage it is more a measure of the bugs in my implementation than some intrinsic false positive rate of Bayesian filtering.  
  
 **Future**  
  
What next? Filtering is an optimization problem, and the key to optimization is profiling. Don't try to guess where your code is slow, because you'll guess wrong. _Look_ at where your code is slow, and fix that. In filtering, this translates to: look at the spams you miss, and figure out what you could have done to catch them.  
  
For example, spammers are now working aggressively to evade filters, and one of the things they're doing is breaking up and misspelling words to prevent filters from recognizing them. But working on this is not my first priority, because I still have no trouble catching these spams [10].  
  
There are two kinds of spams I currently do have trouble with. One is the type that pretends to be an email from a woman inviting you to go chat with her or see her profile on a dating site. These get through because they're the one type of sales pitch you can make without using sales talk. They use the same vocabulary as ordinary email.  
  
The other kind of spams I have trouble filtering are those from companies in e.g. Bulgaria offering contract programming services. These get through because I'm a programmer too, and the spams are full of the same words as my real mail.  
  
I'll probably focus on the personal ad type first. I think if I look closer I'll be able to find statistical differences between these and my real mail. The style of writing is certainly different, though it may take multiword filtering to catch that. Also, I notice they tend to repeat the url, and someone including a url in a legitimate mail wouldn't do that [11].  
  
The outsourcing type are going to be hard to catch. Even if you sent a crawler to the site, you wouldn't find a smoking statistical gun. Maybe the only answer is a central list of domains advertised in spams [12]. But there can't be that many of this type of mail. If the only spams left were unsolicited offers of contract programming services from Bulgaria, we could all probably move on to working on something else.  
  
Will statistical filtering actually get us to that point? I don't know. Right now, for me personally, spam is not a problem. But spammers haven't yet made a serious effort to spoof statistical filters. What will happen when they do?  
  
I'm not optimistic about filters that work at the network level [13]. When there is a static obstacle worth getting past, spammers are pretty efficient at getting past it. There is already a company called Assurance Systems that will run your mail through Spamassassin and tell you whether it will get filtered out.  
  
Network-level filters won't be completely useless. They may be enough to kill all the "opt-in" spam, meaning spam from companies like Virtumundo and Equalamail who claim that they're really running opt-in lists. You can filter those based just on the headers, no matter what they say in the body. But anyone willing to falsify headers or use open relays, presumably including most porn spammers, should be able to get some message past network-level filters if they want to. (By no means the message they'd like to send though, which is something.)  
  
The kind of filters I'm optimistic about are ones that calculate probabilities based on each individual user's mail. These can be much more effective, not only in avoiding false positives, but in filtering too: for example, finding the recipient's email address base-64 encoded anywhere in a message is a very good spam indicator.  
  
But the real advantage of individual filters is that they'll all be different. If everyone's filters have different probabilities, it will make the spammers' optimization loop, what programmers would call their edit-compile-test cycle, appallingly slow. Instead of just tweaking a spam till it gets through a copy of some filter they have on their desktop, they'll have to do a test mailing for each tweak. It would be like programming in a language without an interactive toplevel, and I wouldn't wish that on anyone.  
  
  
  
 **Notes**  
  
[1] Paul Graham. ``A Plan for Spam.'' August 2002. http://paulgraham.com/spam.html.  
  
Probabilities in this algorithm are calculated using a degenerate case of Bayes' Rule. There are two simplifying assumptions: that the probabilities of features (i.e. words) are independent, and that we know nothing about the prior probability of an email being spam.  
  
The first assumption is widespread in text classification. Algorithms that use it are called ``naive Bayesian.''  
  
The second assumption I made because the proportion of spam in my incoming mail fluctuated so much from day to day (indeed, from hour to hour) that the overall prior ratio seemed worthless as a predictor. If you assume that P(spam) and P(nonspam) are both .5, they cancel out and you can remove them from the formula.  
  
If you were doing Bayesian filtering in a situation where the ratio of spam to nonspam was consistently very high or (especially) very low, you could probably improve filter performance by incorporating prior probabilities. To do this right you'd have to track ratios by time of day, because spam and legitimate mail volume both have distinct daily patterns.  
  
[2] Patrick Pantel and Dekang Lin. ``SpamCop-- A Spam Classification & Organization Program.'' Proceedings of AAAI-98 Workshop on Learning for Text Categorization.  
  
[3] Mehran Sahami, Susan Dumais, David Heckerman and Eric Horvitz. ``A Bayesian Approach to Filtering Junk E-Mail.'' Proceedings of AAAI-98 Workshop on Learning for Text Categorization.  
  
[4] At the time I had zero false positives out of about 4,000 legitimate emails. If the next legitimate email was a false positive, this would give us .03%. These false positive rates are untrustworthy, as I explain later. I quote a number here only to emphasize that whatever the false positive rate is, it is less than 1.16%.   
  
[5] Bill Yerazunis. ``Sparse Binary Polynomial Hash Message Filtering and The CRM114 Discriminator.'' Proceedings of 2003 Spam Conference.  
  
[6] In ``A Plan for Spam'' I used thresholds of .99 and .01. It seems justifiable to use thresholds proportionate to the size of the corpora. Since I now have on the order of 10,000 of each type of mail, I use .9999 and .0001.  
  
[7] There is a flaw here I should probably fix. Currently, when ``Subject*foo'' degenerates to just ``foo'', what that means is you're getting the stats for occurrences of ``foo'' in the body or header lines other than those I mark. What I should do is keep track of statistics for ``foo'' overall as well as specific versions, and degenerate from ``Subject*foo'' not to ``foo'' but to ``Anywhere*foo''. Ditto for case: I should degenerate from uppercase to any-case, not lowercase.  
  
It would probably be a win to do this with prices too, e.g. to degenerate from ``$129.99'' to ``$--9.99'', ``$--.99'', and ``$--''.  
  
You could also degenerate from words to their stems, but this would probably only improve filtering rates early on when you had small corpora.  
  
[8] Steven Hauser. ``Statistical Spam Filter Works for Me.'' http://www.sofbot.com.  
  
[9] False positives are not all equal, and we should remember this when comparing techniques for stopping spam. Whereas many of the false positives caused by filters will be near-spams that you wouldn't mind missing, false positives caused by blacklists, for example, will be just mail from people who chose the wrong ISP. In both cases you catch mail that's near spam, but for blacklists nearness is physical, and for filters it's textual.   
  
[10] If spammers get good enough at obscuring tokens for this to be a problem, we can respond by simply removing whitespace, periods, commas, etc. and using a dictionary to pick the words out of the resulting sequence. And of course finding words this way that weren't visible in the original text would in itself be evidence of spam.  
  
Picking out the words won't be trivial. It will require more than just reconstructing word boundaries; spammers both add (``xHot nPorn cSite'') and omit (``P#rn'') letters. Vision research may be useful here, since human vision is the limit that such tricks will approach.  
  
[11] In general, spams are more repetitive than regular email. They want to pound that message home. I currently don't allow duplicates in the top 15 tokens, because you could get a false positive if the sender happens to use some bad word multiple times. (In my current filter, ``dick'' has a spam probabilty of .9999, but it's also a name.) It seems we should at least notice duplication though, so I may try allowing up to two of each token, as Brian Burton does in SpamProbe.  
  
[12] This is what approaches like Brightmail's will degenerate into once spammers are pushed into using mad-lib techniques to generate everything else in the message.  
  
[13] It's sometimes argued that we should be working on filtering at the network level, because it is more efficient. What people usually mean when they say this is: we currently filter at the network level, and we don't want to start over from scratch. But you can't dictate the problem to fit your solution.  
  
Historically, scarce-resource arguments have been the losing side in debates about software design. People only tend to use them to justify choices (inaction in particular) made for other reasons.  
  
 **Thanks** to Sarah Harlin, Trevor Blackwell, and Dan Giffin for reading drafts of this paper, and to Dan again for most of the infrastructure that this filter runs on.  
  
  
  
 **Related:**  
  
  
---  
  
  
---  
| | [A Plan for Spam](spam.html)  
  
  
| | [Plan for Spam FAQ](spamfaq.html)  
  
  
| | [2003 Spam Conference Proceedings](http://spamconference.org/proceedings2003.html)  
  
  
| | [Japanese Translation](http://www.shiro.dreamhost.com/scheme/trans/better-j.html)  
  
  
| | [Chinese Translation](http://people.brandeis.edu/~liji/_private/translation/better.htm)  
  
  
| | [Test of These Suggestions](http://www.bgl.nu/bogofilter/graham.html)  
  
  
  
  
  

***  
  
---