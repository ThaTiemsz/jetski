import React, { Component } from 'react';
import { globalState } from '../state';
import SimpleMarkdown from 'simple-markdown';
import url from 'url';
import punycode from 'punycode';
import highlight from 'highlight.js';

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

  onButton() {
    const { offsetLeft, offsetTop } = this.button;
    Archive.togglePopout(offsetLeft, offsetTop);
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
                <div className="button-3Jq0g9" onclick={() => this.onButton()} ref={el => this.button = el}></div>
                <span className="messageId">({msg.id})</span>
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

class Popout extends Component {
  render() {
    return (
      <div role="dialog" class="noArrow-3BYQ0Z popout-3sVMXz popoutBottom-1YbShG arrowAlignmentTop-iGQczz popoutbottom theme-undefined" style={{
        'z-index': '1001',
        visibility: 'visible',
        left: `${this.props.left + 8}px`,
        top: `${this.props.top + 10}px`,
        transform: 'translateX(-50%) translateY(0%) translateZ(0px)'
      }}>
        <div class="container-3cGP6G" role="menu">
          <button role="menuitem" type="button" class="item-2J1YMK button-38aScr lookBlank-3eh9lL colorBrand-3pXr91 grow-q77ONN">
            <div class="contents-18-Yxp">Raw</div>
          </button>
          <button role="menuitem" type="button" class="item-2J1YMK button-38aScr lookBlank-3eh9lL colorBrand-3pXr91 grow-q77ONN">
            <div class="contents-18-Yxp">Copy User ID</div>
          </button>
          <button role="menuitem" type="button" class="item-2J1YMK button-38aScr lookBlank-3eh9lL colorBrand-3pXr91 grow-q77ONN">
            <div class="contents-18-Yxp">Copy ID</div>
          </button>
        </div>
      </div>
    )
  }
}

export default class Archive extends Component {
  constructor() {
    super();

    this.state = {
      archive: null,
      popout: null
    };

    this.groupBy = this.groupBy.bind(this);
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

  static togglePopout(left, top) {
    this.setState({
      popout: <Popout left={left} top={top} />
    })
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
          {messages.map(m => <Message key={m.id} message={m} />)}
        </div>
      )
    }

    return (
      <div>
        {channels}
        <div className="theme-dark popouts-3dRSmE">
          {this.state.popout}
        </div>
      </div>
    );
  }
}
