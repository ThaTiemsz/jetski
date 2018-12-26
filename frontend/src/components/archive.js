import React, { Component } from 'react';
import { globalState } from '../state';
import SimpleMarkdown from 'simple-markdown';
import url from 'url';
import punycode from 'punycode';
import highlight from 'highlight.js';
import 'highlight.js/styles/solarized-dark.css'

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
        html: (node, output) => {
          return `<a href="${output(node.content)}" className="anchor-3Z-8Bb anchorUnderlineOnHover-2ESHQB" rel="noreferrer noopener" target="_blank">${output(node.content)}</a>`;
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
        html(node, output) {
          return "<br />";
        }
      },
      text: SimpleMarkdown.defaultRules.text,
    
      inlineCode: {
        ...SimpleMarkdown.defaultRules.inlineCode,
        html(node, output) {
          return `<code className="inline">${node.content}</code>`;
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
        html(node, output) {
          return `<span className="mention wrapperHover-1GktnT wrapper-3WhCwL">${node.content}</span>`;
        }
      },
    
      mention: {
        ...SimpleMarkdown.defaultRules.text,
        match(source) {
          return /^<@!?(\d+)>|^(@(?:everyone|here))/.exec(source);
        },
        html(node, output) {
          return `<span className="mention wrapperHover-1GktnT wrapper-3WhCwL">${node.content}</span>`;
        }
      },
    
      channel: {
        ...SimpleMarkdown.defaultRules.text,
        match(source) {
          return /^<#(\d+)>/.exec(source);
        },
        html(node, output) {
          return `<span className="mention wrapperHover-1GktnT wrapper-3WhCwL">${node.content}</span>`;
        }
      },
    
      s: {
        order: SimpleMarkdown.defaultRules.u.order,
        match: SimpleMarkdown.inlineRegex(/^~~([\s\S]+?)~~(?!_)/),
        parse: SimpleMarkdown.defaultRules.u.parse,
        html(node, output) {
          return `<s>${output(node.content)}</s>`;
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
        html(node, output) {
          return `<span className="spoilerText-3p6IlD hidden-HHr2R9"><span className="inlineContent-3ZjPuv">${node.content}</span></span>`;
        }
      }
    };
    
    const parse = SimpleMarkdown.parserFor(DEFAULT_RULES);
    const output = SimpleMarkdown.htmlFor(SimpleMarkdown.ruleOutput(DEFAULT_RULES, 'html'));
    return output(parse(content, {inline: true}));
  }

  getAttachments(attachments) {
    if (attachments.length > 0) {
      attachments = attachments.map(a => `<a href="${a}" target="_blank">${a}</a>`)
      const list = attachments.join(", ")
      return `<span>(<strong>Attachment${attachments.length > 1 ? "s" : ""}</strong>: ${list})</span>`
    } else {
      return
    }
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
                <div className="button-3Jq0g9"></div>
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

export default class Archive extends Component {
  constructor() {
    super();

    this.state = {
      archive: null
    };
  }

  get archiveId() {
    const match = window.location.pathname.match(/([\w-]{36})/);
    if (match) {
      return match[1];
    }
  }

  componentWillMount() {
    globalState.getArchive(this.archiveId).then((archive) => {
      this.setState({archive});
    });
  }

  render() {
    if (!this.state.archive) {
      return <h3>Loading...</h3>;
    }

    let messages = []
    for (const message of this.state.archive.messages) {
      messages.push(
        <Message message={message} />
      );
    }

    return (
      <div className="theme-dark messagesWrapper">
        <Divider name="bot-spam" id="522859278546108416" />
        {messages}
      </div>
    );
  }
}
