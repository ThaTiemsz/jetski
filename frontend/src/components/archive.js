import React, { Component } from 'react';
import { globalState } from '../state';
import SimpleMarkdown from 'simple-markdown';
import url from 'url';
import punycode from 'punycode';
import highlight from 'highlight.js';

function copy(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'absolute';
  textArea.style.top = '-9999px';
  textArea.style.left = '-9999px';
  const body = document.body;
  body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  const success = document.execCommand('copy');
  body.removeChild(textArea);

  return success;
}

class Divider extends Component {
  render() {
    return (
      <div className="divider-3gKybi divider-3zi9LO">
        <span className="dividerContent-2L12VI">#{this.props.name} ({this.props.id})</span>
      </div>
    );
  }
}

class Message extends Component {
  constructor() {
    super();
    this.depunycodeLink = this.depunycodeLink.bind(this);
    this.parseLink = this.parseLink.bind(this);
    this.parseMarkdown = this.parseMarkdown.bind(this);
    this.getAttachments = this.getAttachments.bind(this);
  }

  depunycodeLink(target) {
      try {
        const urlObject = url.parse(target);
        urlObject.hostname = punycode.toASCII(urlObject.hostname || '');
        return url.format(urlObject);
      } catch (e) {
        return target;
      }
  }

  parseLink(capture) {
    const target = this.depunycodeLink(capture[1]);
    return {
      type: 'link',
      content: [
        {
          type: 'text',
          content: target,
        },
      ],
      target,
      title: undefined,
    };
  }

  parseMarkdown(content) {    
    const DEFAULT_RULES = {
      newline: SimpleMarkdown.defaultRules.newline,
      paragraph: SimpleMarkdown.defaultRules.paragraph,
      escape: SimpleMarkdown.defaultRules.escape,
      link: {
        ...SimpleMarkdown.defaultRules.link,
        parse: (capture, parse, state) => {
          return {
            content: parse(capture[1], state),
            target: this.depunycodeLink(SimpleMarkdown.unescapeUrl(capture[2])),
            title: capture[3],
          };
        },
        react: (node, output) => {
          const url = output(node.content)[0].replace("cdn.discordapp.com", "media.discordapp.net");
          return <a href={url} className="anchor-3Z-8Bb anchorUnderlineOnHover-2ESHQB" rel="noreferrer noopener" target="_blank">{url}</a>;
        }
      },
      autolink: {
        ...SimpleMarkdown.defaultRules.autolink,
        parse: this.parseLink,
      },
      url: {
        ...SimpleMarkdown.defaultRules.url,
        parse: this.parseLink,
      },
      strong: SimpleMarkdown.defaultRules.strong,
      em: SimpleMarkdown.defaultRules.em,
      u: SimpleMarkdown.defaultRules.u,
      br: {
        ...SimpleMarkdown.defaultRules.br,
        match(source) {
          return /^\n/.exec(source);
        },
        react(node, output) {
          return <br />;
        }
      },
      text: {
        ...SimpleMarkdown.defaultRules.text,
        react(node, output) {
          const SANITIZE_TEXT_R = /[<>&]/g;
          const SANITIZE_TEXT_CODES = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;'
          };
          const sanitizeText = (text) => String(text).replace(SANITIZE_TEXT_R, (chr) => SANITIZE_TEXT_CODES[chr]);
          return sanitizeText(node.content);
        }
      },
    
      inlineCode: {
        ...SimpleMarkdown.defaultRules.inlineCode,
        react(node, output) {
          return <code className="inline">{node.content}</code>;
        }
      },
    
      // emoticon: {
      //   order: SimpleMarkdown.defaultRules.text.order,
    
      //   match(source) {
      //     // Match emoticons that have slashes in them that would otherwise be escaped.
      //     return /^(Â¯\\_\(ãƒ„\)_\/Â¯)/.exec(source);
      //   },
    
      //   parse(capture) {
      //     return {
      //       type: 'text',
      //       content: capture[1],
      //     };
      //   }
      // },
    
      codeBlock: {
        ...SimpleMarkdown.defaultRules.codeBlock,
        match(source) {
          return /^```(([A-z0-9\-]+?)\n+)?\n*([^]+?)\n*```/.exec(source);
        },
        parse(capture) {
          return {
            lang: (capture[2] || '').trim(),
            content: capture[3] || '',
          };
        },
        react(node, output, state) {
          if (node.lang && highlight.getLanguage(node.lang)) {
            const code = highlight.highlight(node.lang, node.content, true);
            return (
              <pre>
                <code className={'hljs ' + code.language}>
                  {code.value}
                </code>
              </pre>
            );
          } else {
            return (
              <pre>
                <code className="hljs">
                  {output(node.content)}
                </code>
              </pre>
            );
          }
        }
      },
    
      roleMention: {
        ...SimpleMarkdown.defaultRules.text,
        match(source) {
          return /^<@&(\d+)>/.exec(source);
        },
        react(node, output) {
          return <span className="mention wrapperHover-1GktnT wrapper-3WhCwL">{node.content}</span>;
        }
      },
    
      mention: {
        ...SimpleMarkdown.defaultRules.text,
        match(source) {
          return /^<@!?(\d+)>|^(@(?:everyone|here))/.exec(source);
        },
        react(node, output) {
          return <span className="mention wrapperHover-1GktnT wrapper-3WhCwL">{node.content}</span>;
        }
      },
    
      channel: {
        ...SimpleMarkdown.defaultRules.text,
        match(source) {
          return /^<#(\d+)>/.exec(source);
        },
        react(node, output) {
          return <span className="mention wrapperHover-1GktnT wrapper-3WhCwL">{node.content}</span>;
        }
      },

      customEmoji: {
        order: SimpleMarkdown.defaultRules.text.order,
        match(source) {
          return /^<:(\w+):(\d+)>/.exec(source);
        },
        parse(capture) {
          return {
            type: 'text',
            content: `:${capture[1]}:`,
          };
        }
      },
    
      s: {
        order: SimpleMarkdown.defaultRules.u.order,
        match: SimpleMarkdown.inlineRegex(/^~~([\s\S]+?)~~(?!_)/),
        parse: SimpleMarkdown.defaultRules.u.parse,
        react(node, output) {
          return <s>{output(node.content)}</s>;
        }
      },
    
      spoiler: {
        order: SimpleMarkdown.defaultRules.text.order,
        match(source) {
          return /^{{([\s\S]+?)}}/.exec(source);
        },
        parse(capture) {
          return {
            content: capture[1]
          };
        },
        react(node, output) {
          return <span className="spoilerText-3p6IlD hidden-HHr2R9"><span className="inlineContent-3ZjPuv">{node.content}</span></span>;
        }
      }
    };
    
    const parse = SimpleMarkdown.parserFor(DEFAULT_RULES);
    const output = SimpleMarkdown.reactFor(SimpleMarkdown.ruleOutput(DEFAULT_RULES, 'react'));
    return output(parse(content, {inline: true}));
  }

  getAttachments(attachments) {
    if (attachments.length > 0) {
      const list = attachments
        .map(a => <a href={a.replace("cdn.discordapp.com", "media.discordapp.net")} target="_blank">{a.replace("cdn.discordapp.com", "media.discordapp.net")}</a>)
        .reduce((prev, curr) => [prev, ', ', curr])
      return <span>(<strong>Attachment{attachments.length > 1 ? "s" : ""}</strong>: {list})</span>;
    } else {
      return
    }
  }

  onButton(msg) {
    const { offsetLeft, offsetTop } = this.button;
    this.props.popoutCB("options", offsetLeft, offsetTop, msg);
  }

  render() {
    const msg = this.props.message;
    const date = new Date(msg.timestamp);
    const timestamp = date.getTime();
    const isoDate = msg.timestamp.replace(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).\d{6}/, "$1 GMT+0");

    return (
      <div className="containerCompactBounded-cYR5cW containerCompact-3V0ioj container-1YxwTf">
        <div className="messageCompact-kQa7ES message-1PNnaP">
          <div className="contentCompact-1QLHBj content-3dzVd8 containerCompact-3pGPJs container-206Blv">
            <div className="buttonContainer-KtQ8wc">
              <div className="buttonContainer-37UsAw">
                <div className="button-3Jq0g9" onClick={() => this.onButton(msg)} ref={el => this.button = el}></div>
              </div>
            </div>
            <div className="markup-2BOw-j isCompact-1hsne1"><h2 className="headerCompact-3wRt2W"><time className="latin12CompactTimeStamp-3v5WB3 timestampCompact-MHgFLv timestampCompactBase-26h38e" dateTime={timestamp}><i className="separatorLeft-3DZD2Q separator-1xUax1">[</i>{isoDate}<i className="separatorRight-3ctgKv separator-1xUax1">] </i></time><span><span className="username-_4ZSMR">{msg.username}<span className="discriminator">#{msg.discriminator}</span></span><i className="separatorRight-3ctgKv separator-1xUax1">:</i></span></h2> {this.parseMarkdown(msg.content)}<br />{this.getAttachments(msg.attachments)}</div>
          </div>
          <div className="containerCompact-3bB5aN container-1e22Ot"></div>
        </div>
        <hr className="dividerEnabled-2TTlcf divider-32i8lo" />
      </div>
    );
  }
}

class Modal extends Component {
  render() {
    const space = <div style={{width:'1px',height:'0px',padding:'0px',overflow:'hidden',position:'fixed',top:'1px',left:'1px'}}></div>;

    return (
      <div className="theme-dark">
        <div className="backdrop-1wrmKB" onClick={() => this.props.callback(false)} style={{opacity:'0.85','background-color':'rgb(0,0,0)','z-index':'1000','transform':'translateZ(0px)'}}></div>
        <div className="modal-1UGdnR" style={{transform:'scale(1) translateZ(0px)'}}>
          {space}
          {space}
          <div className="inner-1JeGVc">
            <form className="modal-3HD5ck container-SaXBYZ sizeSmall-Sf4iOi">
              <div className="flex-1xMQg5 flex-1O1GKY horizontal-1ae9ci horizontal-2EEEnY flex-1O1GKY directionRow-3v3tfG justifyStart-2NDFzi alignCenter-1dQNNs noWrap-3jynv6 header-1R_AjF" style={{flex:'0 0 auto'}}>
                <h4 className="h4-AQvcAz title-3sZWYQ size16-14cGz5 height20-mO2eIN weightSemiBold-NJexzi defaultColor-1_ajX0 header-3OkTu9">Raw Message</h4>
              </div>
              <div className="content-2BXhLs scrollerThemed-2oenus themeGhostHairline-DBD-2d">
                <div className="inner-3wn6Q5 content-KhOrDM">
                  <div className="spacing-2P-ODW marginBottom20-32qID7 medium-zmzTW- size16-14cGz5 height20-mO2eIN primary-jw0I4K"></div>
                  <div className="message-2qRu38">
                    <div className="containerCozyBounded-1rKFAn containerCozy-jafyvG container-1YxwTf">
                      <div className="messageCozy-2JPAPA message-1PNnaP">
                        <textarea style={{
                          width: '100%',
                          height: '15em',
                          margin: '-20px 0px -26px',
                          border: '0px',
                          'font-family': 'Whitney,Helvetica Neue,Helvetica,Arial,sans-serif',
                          'font-size': '15px'
                        }} readonly>
                          {this.props.msg}
                        </textarea>
                      </div>
                      <hr className="dividerEnabled-2TTlcf divider-32i8lo" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-1xMQg5 flex-1O1GKY horizontalReverse-2eTKWD horizontalReverse-3tRjY7 flex-1O1GKY directionRowReverse-m8IjIq justifyStart-2NDFzi alignStretch-DpGPf3 noWrap-3jynv6 footer-2yfCgX" style={{flex:'0 0 auto'}}>
                <button type="submit" className="button-38aScr lookFilled-1Gx00P colorBrand-3pXr91 sizeMedium-1AC_Sl grow-q77ONN">
                  <div className="contents-18-Yxp" onClick={() => this.props.callback(false)}>Back</div>
                </button>
              </div>
            </form>
          </div>
          {space}
        </div>
      </div>
    );
  }
}

class Popout extends Component {
  render() {
    const type = this.props.type;
    let menu;

    if (type === "options" && this.props.msg && this.props.modalCB) {
      menu = (
        <div className="container-3cGP6G" role="menu">
          <button role="menuitem" type="button" onClick={() => this.props.modalCB(true, this.props.msg.content)} className="item-2J1YMK button-38aScr lookBlank-3eh9lL colorBrand-3pXr91 grow-q77ONN">
            <div className="contents-18-Yxp">Raw</div>
          </button>
          <button role="menuitem" type="button" onClick={() => copy(this.props.msg.author_id)} className="item-2J1YMK button-38aScr lookBlank-3eh9lL colorBrand-3pXr91 grow-q77ONN">
            <div className="contents-18-Yxp">User ID</div>
          </button>
          <button role="menuitem" type="button" onClick={() => copy(this.props.msg.id)} className="item-2J1YMK button-38aScr lookBlank-3eh9lL colorBrand-3pXr91 grow-q77ONN">
            <div className="contents-18-Yxp">Copy ID</div>
          </button>
        </div>
      );
    } else if (type === "format") {
      menu = (
        <div className="popout-2sKjHu lookMinimal-2OMO3G sizeMedium-6vZ9JV filterBrowsingSelectPopout-2kjxuc">
          <div className="optionLabel-2CkCZx optionActive-KkAdqq option-1mJRMP" onClick={() => window.open(`${location.pathname.slice(0, -5)}.html`)}>HTML</div>
          <div className="optionLabel-2CkCZx optionNormal-12VR9V option-1mJRMP" onClick={() => window.open(`${location.pathname.slice(0, -5)}.txt`)}>TXT</div>
          <div className="optionLabel-2CkCZx optionNormal-12VR9V option-1mJRMP" onClick={() => window.open(`${location.pathname.slice(0, -5)}.csv`)}>CSV</div>
          <div className="optionLabel-2CkCZx optionNormal-12VR9V option-1mJRMP" onClick={() => window.open(`${location.pathname.slice(0, -5)}.json`)}>JSON</div>
        </div>
      );
    }

    return (
      <div role="dialog" className="noArrow-3BYQ0Z popout-3sVMXz popoutBottom-1YbShG arrowAlignmentTop-iGQczz popoutbottom theme-undefined" style={{
        'z-index': '1001',
        visibility: 'visible',
        left: `${this.props.left + 8}px`,
        top: `${this.props.top + 10}px`,
        transform: 'translateX(-50%) translateY(0%) translateZ(0px)'
      }}>
        {menu}
      </div>
    );
  }
}

export default class Archive extends Component {
  constructor() {
    super();

    this.state = {
      archive: null,
      popout: {
        type: null,
        component: null,
        msgId: null
      },
      modal: null
    };

    this.groupBy = this.groupBy.bind(this);
    this.togglePopout = this.togglePopout.bind(this);
    this.toggleModal = this.toggleModal.bind(this);
  }

  get archiveId() {
    const match = window.location.pathname.match(/([\w-]{36})/);
    if (match) {
      return match[1];
    }
  }

  componentWillMount() {
    globalState.getArchive(this.archiveId).then((archive) => {
      this.setState({
        archive
      });
    });
  }

  groupBy(items, key) {
    return items.reduce((result, item) => ({
      ...result,
      [item[key]]: [
        ...(result[item[key]] || []),
        item,
      ]
    }), {});
  }

  togglePopout(type, left, top, msg = null) {
    if (type === "options") {
      this.setState({
        popout: {
          type: "options",
          component: this.state.popout.msgId !== msg.id ? <Popout type={type} left={left} top={top} msg={msg} modalCB={this.toggleModal} /> : null,
          msgId: this.state.popout.msgId !== msg.id ? msg.id : null
        }
      });
    } else {
      this.setState({
        popout: {
          type: "format",
          component: this.state.popout.type === "format" ? null : <Popout type={type} left={left} top={top} />,
          msgId: null
        }
      });
    }
  }

  onSelect() {
    const { offsetLeft, offsetTop } = this.select;
    this.togglePopout("format", offsetLeft, offsetTop);
  }

  toggleModal(show, content) {
    this.setState({
      modal: show ? <Modal callback={this.toggleModal} msg={content} /> : null
    });
  }

  render() {
    if (!this.state.archive) {
      return <h3>Loading...</h3>;
    }

    let data = this.groupBy(this.state.archive.messages, "channel_id"); // group by channel
    data = Object.entries(data).sort((a, b) => a[1][0].timestamp - b[1][0].timestamp); // sort by first message chronologically

    let channels = []
    for (const [channel, messages] of data) {
      channels.push(
        <div className="theme-dark messagesWrapper">
          <Divider name={messages[0].channel} id={channel} />
          {messages.map(m => <Message key={m.id} message={m} popoutCB={this.togglePopout} />)}
        </div>
      )
    }

    return (
      <div>
        <div className="theme-dark sortFilterBar-3hePOV">
          <div className="filterAndSort-gLX1Ym">
            <div className="filterBrowsing-20BUwa">
              <label>Format:</label>
              <div className="selectClosed-2un0PJ select-1Pkeg4 lookMinimal-2OMO3G sizeMedium-6vZ9JV filterBrowsingSelectValue-2QrN9m" onClick={() => this.onSelect()} ref={el => this.select = el}>
                <div className="selectLabel-2ltwlE" style={{ flex: '1 1 auto'}}>HTML</div>
                <svg className="arrow-2KJjTM transition-27fFQS directionDown-26e7eE" width="24" height="24" viewBox="0 0 24 24">
                  <path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M7 10L12 15 17 10"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>
        {channels}
        {this.state.modal}
        <div className="theme-dark popouts-3dRSmE">
          {this.state.popout.component}
        </div>
      </div>
    );
  }
}
