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
          <div class="panel-heading">
            <div class="row">
              <div class="col-xs-3">
                <i class={iconClass}></i>
              </div>
              <div class="col-xs-9 text-right">
                <div class="huge">{this.props.data || 'N/A'}</div>
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

    this.state = {
      user: null,
      stats: null,
    };

    globalState.getCurrentUser().then((user) => {
      this.setState({user});
    });

    globalState.getStats().then((stats) => {
      this.setState({stats});
    });
  }

  render() {
    let statsPanels = [];

    if (this.state.user.admin) {
      if (this.state.stats) {
        statsPanels.push(
            <StatsPanel color='primary' icon='comments' data={stats.messages} text='Messages' key='messages' />
        );
        statsPanels.push(
            <StatsPanel color='green' icon='server' data={stats.guilds} text='Guilds' key='guilds' />
        );
        statsPanels.push(
            <StatsPanel color='yellow' icon='user' data={stats.users} text='Users' key='users' />
        );
        statsPanels.push(
            <StatsPanel color='red' icon='hashtag' data={stats.channels} text='Channels' key='channels' />
        );
      }
    }

    return (
      <div className="row">
        {statsPanels}
      </div>
    );
  }
}

class Dashboard extends Component {
  render() {
		return (
      <div>
        <PageHeader name="Dashboard" />
        <div className="row">
          <div className="col-lg-12">
            <DashboardGuildsList />
          </div>
        </div>
        <Stats />
      </div>
    );
  }
}

export default Dashboard;
