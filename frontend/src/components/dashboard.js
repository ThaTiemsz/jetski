import React, { Component } from 'react';

import PageHeader from './page_header';
import GuildsTable from './guilds_table';
import {globalState} from '../state';


class DashboardGuildsList extends Component {
  constructor() {
    super();
    this.state = {guilds: null};
  }

  componentWillMount() {
    globalState.getCurrentUser().then((user) => {
      user.getGuilds().then((guilds) => {
        this.setState({guilds});
      });
    });
  }

  render() {
    return (
      <div className="panel panel-default">
        <div className="panel-heading">
          Guilds
        </div>
        <div className="panel-body">
          <GuildsTable guilds={this.state.guilds}/>
        </div>
      </div>
    );
  }
}

class StatsPanel extends Component {
  render () {
    const panelClass = `panel panel-${this.props.color}`;
    const iconClass = `fa fa-${this.props.icon} fa-5x`;

    return (
      <div className="col-lg-3 col-md-6">
        <div className={panelClass}>
          <div className="panel-heading">
            <div className="row">
              <div className="col-xs-3">
                <i className={iconClass}></i>
              </div>
              <div className="col-xs-9 text-right">
                <div className="huge">{this.props.data || 'N/A'}</div>
                <div>{this.props.text}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

class Stats extends Component {
  constructor() {
    super();
    globalState.getCurrentUser();
  }

  render() {
    let statsPanels = [];

    if (globalState.user.admin) {
      globalState.getStats((stats) => {
        return (
          <div>
            <StatsPanel color='primary' icon='comments' data={globalState.stats.messages} text='Messages' key='messages' />
            <StatsPanel color='green' icon='server' data={globalState.stats.guilds} text='Guilds' key='guilds' />
            <StatsPanel color='yellow' icon='user' data={globalState.stats.users} text='Users' key='users' />
            <StatsPanel color='red' icon='hashtag' data={globalState.stats.channels} text='Channels' key='channels' />
          </div>
        );
      });
      return (null);
    } else {
      return (null);
    }
  }
}

class Dashboard extends Component {
  render() {
		return (
      <div>
        <PageHeader name="Dashboard" />
        <div className="row">
          <Stats />
        </div>
        <div className="row">
          <div className="col-lg-12">
            <DashboardGuildsList />
          </div>
        </div>
      </div>
    );
  }
}

export default Dashboard;
